"""Measure extraction consistency across models/settings.

Runs the real extraction path N times per syllabus and scores each result
against hand-checked invariants, so a config is judged on how often it gets
the same right answer - not on one lucky run.

    .venv/bin/python scripts/extraction_eval.py --trials 5 --model gpt-5.4-nano
"""
import argparse, asyncio, base64, json, statistics, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import AsyncOpenAI
from app.config import OPENAI_API_KEY
import importlib
from app.schemas.extraction import SyllabusExtraction
from app.services.openai_extraction import INSTRUCTIONS

SYLLABI = Path(__file__).resolve().parent.parent.parent / "Test_Syllabi"

def pdf_input(path: Path, detail: str):
    b64 = base64.b64encode(path.read_bytes()).decode()
    return [
        {"type": "input_file", "filename": path.name,
         "file_data": f"data:application/pdf;base64,{b64}", "detail": detail},
        {"type": "input_text", "text": (
            "Read this syllabus PDF and extract structured calendar/task data. "
            "Use both the PDF text and page images. If the PDF includes scans, tables, "
            "or unusual formatting, inspect the visible page content rather than returning an error.")},
    ]

async def run_once(client, path, model, detail, effort, instructions, temperature=None, schema=None):
    req = {
        "model": model,
        "instructions": instructions,
        "input": [{"role": "user", "content": pdf_input(path, detail)}],
        "text_format": schema or SyllabusExtraction,
        "prompt_cache_key": "syllabus-eval-v1",
    }
    if effort:
        req["reasoning"] = {"effort": effort}
    if temperature is not None:
        req["temperature"] = temperature
    t0 = time.time()
    try:
        r = await client.responses.parse(**req)
        return {"ok": True, "parsed": r.output_parsed, "secs": time.time() - t0,
                "in_tok": r.usage.input_tokens, "out_tok": r.usage.output_tokens}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "secs": time.time() - t0}

# ---- scoring -------------------------------------------------------------
def all_dates(d):
    out = []
    for m in d.class_schedule.meetings:
        out += [m.start_date, m.end_date]
    for coll in (d.class_cancellations, d.events):
        out += [i.date for i in coll]
    out += [i.due_date for i in d.tasks] + [i.due_date for i in d.readings]
    return [x for x in out if x]

def meeting_days(d):
    return {frozenset(m.days_of_week) for m in d.class_schedule.meetings if m.days_of_week}

def check(name, ok):
    return (name, bool(ok))

def score_stat190(d):
    days = meeting_days(d)
    lecture = [m for m in d.class_schedule.meetings
               if set(m.days_of_week) == {"Tuesday", "Thursday"}]
    dates = all_dates(d)
    ev = {(e.date, e.event_type) for e in d.events}
    canc = {c.date for c in d.class_cancellations}
    return [
        check("schedule.found", d.class_schedule.found),
        check("has TR lecture", bool(lecture)),
        check("lecture 14:00-15:15", any(m.start_time == "14:00" and m.end_time == "15:15" for m in lecture)),
        check("all dates in 2026", bool(dates) and all(x.startswith("2026") for x in dates)),
        check("dates within term", all("2026-01-19" <= x <= "2026-05-10" for x in dates)),
        check("final exam 2026-05-09", any(dt == "2026-05-09" and t == "final_exam" for dt, t in ev)),
        check("midterm 2026-03-05", any(dt == "2026-03-05" for dt, _ in ev)),
        check("spring break 03-10", "2026-03-10" in canc),
        check("spring break 03-12", "2026-03-12" in canc),
        check("no phantom weekly task", not d.tasks),
        check("only the TR lecture", len(d.class_schedule.meetings) == 1),
        check("no topic-as-reading", not d.readings),
    ] + shared_checks(d)

def shared_checks(d):
    """Structural faults that make an item unusable downstream, whatever the syllabus."""
    ms = d.class_schedule.meetings
    # location is part of the identity: a course can run two sections at the same
    # day and time in different rooms, and those are genuinely separate meetings.
    sigs = [(tuple(sorted(m.days_of_week)), m.start_time, m.end_time, m.title, m.location)
            for m in ms]
    return [
        check("no dayless meeting", all(m.days_of_week for m in ms)),
        check("no duplicate meeting", len(sigs) == len(set(sigs))),
    ]

def score_generic(d):
    dates = all_dates(d)
    return [
        check("schedule.found", d.class_schedule.found),
        check("has meetings", bool(d.class_schedule.meetings)),
        check("dates well formed", all(len(x) == 10 and x[4] == "-" for x in dates)),
    ] + shared_checks(d)

SCORERS = {"STAT190_Spring2026.pdf": score_stat190}

# ---- shape fingerprint (consistency, independent of correctness) ---------
def fingerprint(d):
    return json.dumps({
        "meetings": sorted(
            [f"{sorted(m.days_of_week)}|{m.start_time}|{m.end_time}" for m in d.class_schedule.meetings]),
        "n_events": len(d.events), "n_tasks": len(d.tasks),
        "n_readings": len(d.readings), "n_canc": len(d.class_cancellations),
    }, sort_keys=True)

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt-5.4-nano")
    ap.add_argument("--detail", default="auto")
    ap.add_argument("--effort", default=None)
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--files", nargs="*", default=None)
    ap.add_argument("--instructions-file", default=None)
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--show-shapes", action="store_true")
    ap.add_argument("--temperature", type=float, default=None)
    ap.add_argument("--schema-module", default=None)
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--save-raw", default=None)
    a = ap.parse_args()

    instructions = Path(a.instructions_file).read_text() if a.instructions_file else INSTRUCTIONS
    files = [SYLLABI / f for f in a.files] if a.files else sorted(SYLLABI.glob("*.pdf"))
    schema = (importlib.import_module(a.schema_module).SyllabusExtraction
              if a.schema_module else None)
    client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=600, max_retries=2)

    label = f"{a.model} detail={a.detail} effort={a.effort or 'default'} temp={a.temperature}"
    print(f"\n=== {label}  ({a.trials} trials/file) ===")
    report = {"config": vars(a), "files": {}}

    sem = asyncio.Semaphore(a.concurrency)

    async def limited(path):
        # The org TPM ceiling is low enough that a wide fan-out fails runs on 429
        # rather than on anything the config did, which would corrupt the scores.
        async with sem:
            return await run_once(client, path, a.model, a.detail, a.effort,
                                  instructions, a.temperature, schema)

    for path in files:
        results = await asyncio.gather(*[limited(path) for _ in range(a.trials)])
        good = [r for r in results if r["ok"]]
        scorer = SCORERS.get(path.name, score_generic)
        names, tallies = [], {}
        for r in good:
            for n, ok in scorer(r["parsed"]):
                tallies.setdefault(n, []).append(ok)
                if n not in names: names.append(n)
        fps = [fingerprint(r["parsed"]) for r in good]
        modal = max(set(fps), key=fps.count) if fps else None
        per_run = [sum(1 for _, ok in scorer(r["parsed"]) if ok) for r in good]
        total_checks = len(names)
        file_rep = {
            "errors": [r["error"] for r in results if not r["ok"]],
            "checks": {n: sum(tallies[n]) for n in names},
            "trials": len(good),
            "perfect_runs": sum(1 for s in per_run if s == total_checks),
            "shape_agreement": round(fps.count(modal) / len(fps), 2) if fps else 0,
            "secs": round(statistics.mean([r["secs"] for r in good]), 1) if good else None,
            "in_tok": round(statistics.mean([r["in_tok"] for r in good])) if good else None,
            "out_tok": round(statistics.mean([r["out_tok"] for r in good])) if good else None,
        }
        report["files"][path.name] = file_rep
        if a.save_raw:
            raw_dir = Path(a.save_raw); raw_dir.mkdir(parents=True, exist_ok=True)
            (raw_dir / f"{path.stem}.json").write_text(json.dumps(
                [r["parsed"].model_dump() for r in good], indent=2))
        print(f"\n{path.name}")
        print(f"  ok {len(good)}/{a.trials}   perfect {file_rep['perfect_runs']}/{len(good)}"
              f"   shape-agree {file_rep['shape_agreement']}"
              f"   {file_rep['secs']}s  in={file_rep['in_tok']} out={file_rep['out_tok']}")
        for n in names:
            hits = sum(tallies[n])
            flag = "  " if hits == len(good) else "<<"
            print(f"   {flag} {hits}/{len(good)}  {n}")
        for e in file_rep["errors"][:2]:
            print(f"    ERROR {e[:160]}")
        if a.show_shapes:
            for fp in sorted(set(fps), key=fps.count, reverse=True):
                d = json.loads(fp)
                print(f"    x{fps.count(fp)}  ev={d['n_events']} task={d['n_tasks']} "
                      f"read={d['n_readings']} canc={d['n_canc']} meet={d['meetings']}")

    if a.json_out:
        Path(a.json_out).write_text(json.dumps(report, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
