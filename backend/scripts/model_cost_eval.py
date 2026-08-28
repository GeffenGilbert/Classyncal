"""Compare model / PDF-detail / reasoning settings on extraction accuracy and cost.

Uses the production prompt and schema unchanged - the question here is what the
knobs outside the prompt are worth, so changing the prompt at the same time would
make the answer unreadable.

Accuracy is per category, item by item: each expected item from scripts/truth.py is
matched against the extracted items on its date, so a category is scored on getting
the right things, not the right number of things. Cost is computed from the token
usage the API actually reports, including cached input and reasoning tokens, and
reported per 1000 extractions.

    .venv/bin/python scripts/model_cost_eval.py --trials 6
"""
import argparse, asyncio, base64, json, statistics, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import AsyncOpenAI

from app.config import OPENAI_API_KEY
from app.schemas.extraction import SyllabusExtraction
from app.services.openai_extraction import INSTRUCTIONS
from truth import TRUTH, CATEGORIES

SYLLABI = Path(__file__).resolve().parent.parent.parent / "Test_Syllabi"

# USD per 1M tokens, from developers.openai.com/api/docs/pricing, checked 2026-08-26.
PRICING = {
    "gpt-5.4-nano": {"in": 0.20, "cached": 0.02, "out": 1.25},
    "gpt-5.4-mini": {"in": 0.75, "cached": 0.075, "out": 4.50},
    "gpt-5.4": {"in": 2.50, "cached": 0.25, "out": 15.00},
    # Priced at nano level despite being a newer generation - which is the whole
    # reason it is worth testing here.
    "gpt-5.6-luna": {"in": 0.20, "cached": 0.02, "out": 1.20},
    "gpt-5.6-terra": {"in": 2.00, "cached": 0.20, "out": 12.00},
    "gpt-5.6-sol": {"in": 4.00, "cached": 0.40, "out": 20.00},
}

# The configs under test. Each varies exactly one thing from the one above it so a
# difference in the table can be attributed to a single knob.
CONFIGS = [
    ("nano auto (production)", {"model": "gpt-5.4-nano", "detail": "auto", "effort": None}),
    ("nano auto +reason:low", {"model": "gpt-5.4-nano", "detail": "auto", "effort": "low"}),
    ("mini auto", {"model": "gpt-5.4-mini", "detail": "auto", "effort": None}),
    ("mini high-detail", {"model": "gpt-5.4-mini", "detail": "high", "effort": None}),
    ("mini auto +reason:low", {"model": "gpt-5.4-mini", "detail": "auto", "effort": "low"}),
    ("luna auto (default)", {"model": "gpt-5.6-luna", "detail": "auto", "effort": None}),
]


def pdf_input(path, detail):
    """The same content block the production upload path builds."""
    b64 = base64.b64encode(path.read_bytes()).decode()
    return [
        {"type": "input_file", "filename": path.name,
         "file_data": f"data:application/pdf;base64,{b64}", "detail": detail},
        {"type": "input_text", "text": (
            "Read this syllabus PDF and extract structured calendar/task data. "
            "Use both the PDF text and page images. If the PDF includes scans, tables, "
            "or unusual formatting, inspect the visible page content rather than returning an error.")},
    ]


async def run_once(client, path, cfg):
    req = {
        "model": cfg["model"],
        "instructions": INSTRUCTIONS,
        "input": [{"role": "user", "content": pdf_input(path, cfg["detail"])}],
        "text_format": SyllabusExtraction,
        # Distinct per config: a shared key across models would report cache hits
        # that the cheaper config never actually got.
        "prompt_cache_key": f"eval-{cfg['model']}-{cfg['detail']}-{cfg['effort']}",
    }
    if cfg["effort"]:
        req["reasoning"] = {"effort": cfg["effort"]}
    t0 = time.time()
    try:
        r = await client.responses.parse(**req)
        u = r.usage
        cached = getattr(getattr(u, "input_tokens_details", None), "cached_tokens", 0) or 0
        reasoning = getattr(getattr(u, "output_tokens_details", None), "reasoning_tokens", 0) or 0
        return {"ok": True, "parsed": r.output_parsed, "secs": time.time() - t0,
                "in_tok": u.input_tokens, "cached_tok": cached,
                "out_tok": u.output_tokens, "reasoning_tok": reasoning}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "secs": time.time() - t0}


# ---- scoring -------------------------------------------------------------
def extracted(doc):
    """Flatten a parsed extraction into the five scored categories."""
    return {
        "meetings": [
            {"days": sorted(m.days_of_week), "start_time": m.start_time,
             "end_time": m.end_time, "start_date": m.start_date,
             "end_date": m.end_date, "title": m.title}
            for m in doc.class_schedule.meetings
        ],
        "events": [{"date": e.date, "title": e.title} for e in doc.events],
        "tasks": [{"date": t.due_date, "title": t.title} for t in doc.tasks],
        "readings": [{"date": r.due_date, "title": r.title} for r in doc.readings],
        "cancellations": [{"date": c.date, "title": f"{c.title} {c.reason or ''}"}
                          for c in doc.class_cancellations],
    }


def match_dated(want, got):
    """Pair expected items with extracted ones sharing their date.

    Two passes, because one greedy pass depends on the order of `want`: two truth
    items on the same date let whichever comes first take the item the second one
    would have matched by title. So every keyword match is claimed first, and only
    then are the leftovers paired on date alone.
    Returns (hit_date, hit_date_and_title, spurious).
    """
    free = set(range(len(got)))
    unmatched = []
    hit_date = hit_title = 0

    for w in want:
        kw = w["kw"].lower()
        titled = [i for i in free
                  if got[i]["date"] == w["date"] and kw in (got[i]["title"] or "").lower()]
        if titled:
            free.discard(titled[0])
            hit_date += 1
            hit_title += 1
        else:
            unmatched.append(w)

    for w in unmatched:
        same_date = [i for i in free if got[i]["date"] == w["date"]]
        if same_date:
            free.discard(same_date[0])
            hit_date += 1

    return hit_date, hit_title, len(free)


def match_meetings(want, got):
    """A meeting is right only if its days and both times are right.

    Those three decide whether the recurring event lands correctly in the calendar;
    start/end date is scored separately since it only shifts the series' extent.
    """
    free = list(range(len(got)))
    hit = hit_dates = 0
    for w in want:
        cand = [i for i in free
                if got[i]["days"] == sorted(w["days"])
                and got[i]["start_time"] == w["start_time"]
                and got[i]["end_time"] == w["end_time"]]
        if not cand:
            continue
        i = cand[0]
        free.remove(i)
        hit += 1
        if got[i]["start_date"] == w["start_date"] and got[i]["end_date"] == w["end_date"]:
            hit_dates += 1
    return hit, hit_dates, len(free)


def score(doc, truth):
    got = extracted(doc)
    out = {}
    for cat in CATEGORIES:
        want = truth[cat]
        if cat == "meetings":
            hit, extra_ok, spur = match_meetings(want, got[cat])
            out[cat] = {"want": len(want), "got": len(got[cat]), "hit": hit,
                        "strict": extra_ok, "spurious": spur}
        else:
            hit, strict, spur = match_dated(want, got[cat])
            out[cat] = {"want": len(want), "got": len(got[cat]), "hit": hit,
                        "strict": strict, "spurious": spur}
    return out


def cost_usd(model, in_tok, cached_tok, out_tok):
    p = PRICING[model]
    fresh = max(in_tok - cached_tok, 0)
    return (fresh * p["in"] + cached_tok * p["cached"] + out_tok * p["out"]) / 1_000_000


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=6)
    ap.add_argument("--files", nargs="*", default=["Psyc 161 Syllabus.pdf"])
    ap.add_argument("--configs", nargs="*", default=None,
                    help="Substrings of config labels to include; default is all.")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--out-dir", default="/tmp/cost_eval")
    a = ap.parse_args()

    configs = CONFIGS
    if a.configs:
        configs = [c for c in CONFIGS if any(s in c[0] for s in a.configs)]

    client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=900, max_retries=3)
    # The org TPM ceiling is low enough that a wide fan-out fails runs on 429 rather
    # than on anything the config did, which would corrupt the scores.
    sem = asyncio.Semaphore(a.concurrency)

    async def limited(path, cfg):
        async with sem:
            return await run_once(client, path, cfg)

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {}

    for fname in a.files:
        path = SYLLABI / fname
        truth = TRUTH[fname]
        print(f"\n{'=' * 100}\n{fname}   ({a.trials} trials per config)\n{'=' * 100}")
        print("expected: " + ", ".join(f"{c}={len(truth[c])}" for c in CATEGORIES))

        for label, cfg in configs:
            results = await asyncio.gather(*[limited(path, cfg) for _ in range(a.trials)])
            good = [r for r in results if r["ok"]]
            if not good:
                print(f"\n{label}: all {a.trials} runs failed - {results[0]['error'][:160]}")
                continue

            scores = [score(r["parsed"], truth) for r in good]
            per_cat = {}
            for cat in CATEGORIES:
                per_cat[cat] = {
                    "want": len(truth[cat]),
                    "hit": statistics.mean(s[cat]["hit"] for s in scores),
                    "strict": statistics.mean(s[cat]["strict"] for s in scores),
                    "spurious": statistics.mean(s[cat]["spurious"] for s in scores),
                    "got": statistics.mean(s[cat]["got"] for s in scores),
                }
            # A run is "clean" only if every category is fully right with nothing
            # extra - that is what a user who does not want to edit anything sees.
            clean = sum(1 for s in scores
                        if all(s[c]["hit"] == s[c]["want"] and s[c]["spurious"] == 0
                               for c in CATEGORIES))
            mean_in = statistics.mean(r["in_tok"] for r in good)
            mean_cached = statistics.mean(r["cached_tok"] for r in good)
            mean_out = statistics.mean(r["out_tok"] for r in good)
            mean_reason = statistics.mean(r["reasoning_tok"] for r in good)
            per_run = cost_usd(cfg["model"], mean_in, mean_cached, mean_out)

            rec = {"config": cfg, "ok": len(good), "trials": a.trials, "clean": clean,
                   "categories": per_cat, "secs": statistics.mean(r["secs"] for r in good),
                   "in_tok": mean_in, "cached_tok": mean_cached, "out_tok": mean_out,
                   "reasoning_tok": mean_reason, "usd_per_1000": per_run * 1000}
            report[f"{fname}::{label}"] = rec

            print(f"\n--- {label} ---")
            print(f"  ok {len(good)}/{a.trials}   fully-clean runs {clean}/{len(good)}"
                  f"   {rec['secs']:.1f}s")
            print(f"  tokens: in={mean_in:,.0f} (cached {mean_cached:,.0f})"
                  f"  out={mean_out:,.0f} (reasoning {mean_reason:,.0f})")
            print(f"  cost: ${per_run:.4f}/extraction   ${per_run * 1000:,.2f} per 1000")
            print(f"  {'category':14s}{'want':>6s}{'found':>8s}{'correct':>9s}"
                  f"{'+title':>8s}{'spurious':>10s}")
            for cat in CATEGORIES:
                c = per_cat[cat]
                print(f"  {cat:14s}{c['want']:>6d}{c['got']:>8.1f}{c['hit']:>9.1f}"
                      f"{c['strict']:>8.1f}{c['spurious']:>10.1f}")

            (out_dir / f"{Path(fname).stem}__{label.replace(' ', '_')}.json").write_text(
                json.dumps([r["parsed"].model_dump() for r in good], indent=2))

    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    print(f"\nraw runs + report.json in {out_dir}")


if __name__ == "__main__":
    asyncio.run(main())
