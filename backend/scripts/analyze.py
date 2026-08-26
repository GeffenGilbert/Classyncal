"""Re-score the saved eval runs offline and price them the way production will pay.

Separate from model_cost_eval.py because everything here is free to re-run: the
answer key and the cost model both changed after the API calls were already made,
and re-running the calls to apply them would be pure waste.

Two corrections over the live output:

1. `soft` truth items are excluded. Two items on the Psyc key are genuinely
   ambiguous, and no config ever found them - leaving them in made every config
   score 0/8 "clean" runs, which hides the differences between configs.

2. Cost is recomputed with no cache credit. The eval sent the *same* PDF 8 times
   per config, so the API reported 6-8k cached input tokens. In production every
   upload is a different PDF, so only the ~1k instruction prefix can ever hit the
   cache. Pricing the measured cache hits would understate the real bill by ~40%.
"""
import json, statistics, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.schemas.extraction import SyllabusExtraction
from model_cost_eval import score, PRICING, CONFIGS
from truth import TRUTH, CATEGORIES

RAW = Path("/tmp/cost_eval")
REPORT = json.load(open(RAW / "report.json"))


def hard_truth(truth):
    """The answer key minus the items two careful readers would disagree about."""
    return {c: [i for i in truth[c] if not i.get("soft")] for c in CATEGORIES}


def uncached_usd(model, in_tok, out_tok):
    """Per-extraction cost assuming a cold cache, which is the production case."""
    p = PRICING[model]
    return (in_tok * p["in"] + out_tok * p["out"]) / 1_000_000


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default="/tmp/cost_eval")
    ap.add_argument("--file", default="Psyc 161 Syllabus.pdf")
    a = ap.parse_args()

    global RAW, REPORT
    RAW = Path(a.raw_dir)
    REPORT = json.load(open(RAW / "report.json"))

    fname = a.file
    truth = hard_truth(TRUTH[fname])
    totals = {c: len(truth[c]) for c in CATEGORIES}
    grand = sum(totals.values())

    print(f"\n{fname} - soft/ambiguous items excluded")
    print("expected: " + ", ".join(f"{c}={totals[c]}" for c in CATEGORIES)
          + f"  (total {grand})")

    rows = []
    for label, cfg in CONFIGS:
        path = RAW / f"{Path(fname).stem}__{label.replace(' ', '_')}.json"
        if not path.exists():
            continue
        runs = [SyllabusExtraction(**d) for d in json.load(open(path))]
        scores = [score(r, truth) for r in runs]
        rec = REPORT[f"{fname}::{label}"]

        per_cat = {c: statistics.mean(s[c]["hit"] for s in scores) for c in CATEGORIES}
        spurious = {c: statistics.mean(s[c]["spurious"] for s in scores) for c in CATEGORIES}
        correct = sum(per_cat.values())
        extra = sum(spurious.values())
        clean = sum(1 for s in scores
                    if all(s[c]["hit"] == totals[c] and s[c]["spurious"] == 0
                           for c in CATEGORIES))
        # Per-run spread on the category that actually separates these configs.
        task_hits = sorted(s["tasks"]["hit"] for s in scores)

        usd = uncached_usd(cfg["model"], rec["in_tok"], rec["out_tok"])
        rows.append({
            "label": label, "correct": correct, "extra": extra, "clean": clean,
            "n": len(runs), "per_cat": per_cat, "spurious": spurious,
            "usd_1k": usd * 1000, "secs": rec["secs"], "tasks": task_hits,
            "in_tok": rec["in_tok"], "out_tok": rec["out_tok"],
        })

    print(f"\n{'config':24s}{'correct':>12s}{'spurious':>10s}{'clean':>8s}"
          f"{'$/1000':>10s}{'secs':>7s}")
    print("-" * 71)
    for r in rows:
        print(f"{r['label']:24s}{r['correct']:>7.1f}/{grand:<4d}{r['extra']:>10.1f}"
              f"{r['clean']:>5d}/{r['n']:<2d}{r['usd_1k']:>10.2f}{r['secs']:>7.1f}")

    print(f"\nper-category items correct (of {grand} total)")
    print(f"{'config':24s}" + "".join(f"{c[:9]:>13s}" for c in CATEGORIES))
    print("-" * 89)
    print(f"{'(expected)':24s}" + "".join(f"{totals[c]:>13d}" for c in CATEGORIES))
    for r in rows:
        print(f"{r['label']:24s}" + "".join(f"{r['per_cat'][c]:>13.1f}" for c in CATEGORIES))

    print(f"\nspurious items invented (lower is better)")
    print(f"{'config':24s}" + "".join(f"{c[:9]:>13s}" for c in CATEGORIES))
    print("-" * 89)
    for r in rows:
        print(f"{r['label']:24s}" + "".join(f"{r['spurious'][c]:>13.1f}" for c in CATEGORIES))

    print(f"\ntasks correct per run (of {totals['tasks']}) - the category that separates configs")
    for r in rows:
        dist = " ".join(f"{v}x{n}" for v, n in Counter(r["tasks"]).most_common())
        print(f"  {r['label']:24s} {dist}")

    base = next(r for r in rows if "production" in r["label"])
    print(f"\nvs production baseline ({base['usd_1k']:.2f} per 1000)")
    for r in rows:
        if r is base:
            continue
        d_corr = r["correct"] - base["correct"]
        d_cost = r["usd_1k"] - base["usd_1k"]
        print(f"  {r['label']:24s} {d_corr:+5.1f} items  {d_cost:+7.2f} per 1000"
              f"   ({r['usd_1k'] / base['usd_1k']:.1f}x)")


if __name__ == "__main__":
    main()
