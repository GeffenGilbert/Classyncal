"""Cross-file, cross-config summary over every eval batch run so far.

The batches live in separate raw dirs because they were run as separate questions;
this pulls them together so a config can be compared on all four syllabi at once.
Costs are cold-cache (see analyze.py for why the eval's own cache credit is not
representative of production).
"""
import json, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.schemas.extraction import SyllabusExtraction
from model_cost_eval import score, PRICING
from truth import TRUTH, CATEGORIES

RAW_DIRS = ["/tmp/cost_eval", "/tmp/cost_eval_stat", "/tmp/cost_eval_easy",
            "/tmp/cost_eval_luna"]

FILES = ["Psyc 161 Syllabus.pdf", "STAT190_Spring2026.pdf",
         "CSC 242 Artificial Intelligence (Spring 2026).pdf",
         "Bio110 2025 syllabus v2.pdf"]
SHORT = {FILES[0]: "Psyc161", FILES[1]: "STAT190", FILES[2]: "CSC242", FILES[3]: "Bio110"}

ORDER = ["nano auto (production)", "luna auto (default)", "nano auto +reason:low",
         "mini auto", "mini high-detail", "mini auto +reason:low"]


def hard(truth):
    return {c: [i for i in truth[c] if not i.get("soft")] for c in CATEGORIES}


def load():
    """cell[(file, config)] = {correct, total, spurious, usd_1k}"""
    cells = {}
    for d in RAW_DIRS:
        rep_path = Path(d) / "report.json"
        if not rep_path.exists():
            continue
        report = json.load(open(rep_path))
        for key, rec in report.items():
            fname, label = key.split("::", 1)
            raw = Path(d) / f"{Path(fname).stem}__{label.replace(' ', '_')}.json"
            if not raw.exists():
                continue
            truth = hard(TRUTH[fname])
            total = sum(len(truth[c]) for c in CATEGORIES)
            scores = [score(SyllabusExtraction(**x), truth) for x in json.load(open(raw))]
            correct = statistics.mean(sum(s[c]["hit"] for c in CATEGORIES) for s in scores)
            spur = statistics.mean(sum(s[c]["spurious"] for c in CATEGORIES) for s in scores)
            p = PRICING[rec["config"]["model"]]
            usd = (rec["in_tok"] * p["in"] + rec["out_tok"] * p["out"]) / 1_000_000
            cells[(fname, label)] = {
                "correct": correct, "total": total, "spurious": spur,
                "usd_1k": usd * 1000, "secs": rec["secs"],
                "in_tok": rec["in_tok"], "out_tok": rec["out_tok"],
                "reasoning_tok": rec["reasoning_tok"], "n": len(scores),
            }
    return cells


def main():
    cells = load()
    labels = [l for l in ORDER if any(k[1] == l for k in cells)]

    print("\nITEMS CORRECT (of hand-checked total) - higher is better")
    print(f"{'config':24s}" + "".join(f"{SHORT[f]:>16s}" for f in FILES))
    print(f"{'':24s}" + "".join(f"{'(of ' + str(next((c['total'] for (ff, _), c in cells.items() if ff == f), 0)) + ')':>16s}" for f in FILES))
    print("-" * 88)
    for label in labels:
        row = f"{label:24s}"
        for f in FILES:
            c = cells.get((f, label))
            row += f"{c['correct']:>10.1f}      " if c else f"{'-':>16s}"
        print(row)

    print("\nSPURIOUS ITEMS INVENTED per run - lower is better")
    print(f"{'config':24s}" + "".join(f"{SHORT[f]:>16s}" for f in FILES))
    print("-" * 88)
    for label in labels:
        row = f"{label:24s}"
        for f in FILES:
            c = cells.get((f, label))
            row += f"{c['spurious']:>10.1f}      " if c else f"{'-':>16s}"
        print(row)

    print("\nCOST per 1000 extractions (cold cache) and mean latency")
    print(f"{'config':24s}{'$/1000 avg':>12s}{'range':>18s}{'secs':>8s}"
          f"{'reasoning tok':>15s}{'files':>7s}")
    print("-" * 84)
    base = None
    for label in labels:
        cs = [cells[(f, label)] for f in FILES if (f, label) in cells]
        avg = statistics.mean(c["usd_1k"] for c in cs)
        lo, hi = min(c["usd_1k"] for c in cs), max(c["usd_1k"] for c in cs)
        secs = statistics.mean(c["secs"] for c in cs)
        rt = statistics.mean(c["reasoning_tok"] for c in cs)
        if label == "nano auto (production)":
            base = avg
        mult = f"  ({avg / base:.1f}x)" if base else ""
        print(f"{label:24s}{avg:>12.2f}{f'{lo:.2f}-{hi:.2f}':>18s}{secs:>8.1f}"
              f"{rt:>15.0f}{len(cs):>7d}{mult}")

    print("\nCOMPARABLE-ON-ALL-FOUR configs only")
    common = [l for l in labels
              if all((f, l) in cells for f in FILES)]
    for label in common:
        cs = [cells[(f, label)] for f in FILES]
        corr = sum(c["correct"] for c in cs)
        tot = sum(c["total"] for c in cs)
        spur = sum(c["spurious"] for c in cs)
        avg = statistics.mean(c["usd_1k"] for c in cs)
        print(f"  {label:24s} {corr:5.1f}/{tot} items  {spur:5.1f} invented"
              f"  ${avg:.2f}/1000")


if __name__ == "__main__":
    main()
