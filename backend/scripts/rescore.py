"""Re-score saved extraction runs on per-category counts.

Run-to-run identity is not the goal - what matters is that each category lands on
the right number, with only cosmetic differences between runs. This prints the
distribution of counts per category so a config is judged on where it centres and
how tightly, not on whether two runs matched byte for byte.
"""
import json, sys
from collections import Counter
from pathlib import Path

CONFIGS = [("nano (production)", "/tmp/raw_nano"),
           ("mini + v2/v3", "/tmp/raw_mini_v3"),
           ("mini + v5 (generic)", "/tmp/raw_v5")]

CATS = ["meetings", "events", "tasks", "readings", "cancellations"]

def counts(run):
    return {
        "meetings": len(run["class_schedule"]["meetings"]),
        "events": len(run["events"]),
        "tasks": len(run["tasks"]),
        "readings": len(run["readings"]),
        "cancellations": len(run["class_cancellations"]),
    }

def fmt(dist, truth=None):
    """Most common first; mark the value matching hand-checked truth."""
    parts = []
    for val, n in dist.most_common():
        mark = "*" if truth is not None and val == truth else ""
        parts.append(f"{val}{mark}x{n}")
    return " ".join(parts)

# Hand-derived from reading the PDF; None where not yet established.
TRUTH = {
    "STAT190_Spring2026": {"meetings": 1, "events": 2, "tasks": 0,
                           "readings": 0, "cancellations": 2},
    # Psyc 161: header states MW 3:25-4:40 as the only recurring pattern. The lone
    # 1/23 (F) row is a one-off session, not a second weekly meeting. Events are
    # Exam 1 (2/23), Exam 2 (4/6) and that Friday session; Exam 3 is TBA with no
    # date, so it is correctly dropped. Tasks are 3 essays + 7 questionnaire rows
    # + 4 extra-credit questionnaires.
    "Psyc 161 Syllabus": {"meetings": 1, "events": 3, "tasks": 14,
                          "readings": 9, "cancellations": 2},
}

files = sorted({p.stem for _, d in CONFIGS for p in Path(d).glob("*.json")})
for stem in files:
    truth = TRUTH.get(stem, {})
    print(f"\n=== {stem} ===")
    if truth:
        print("    hand-checked truth: " + ", ".join(f"{k}={v}" for k, v in truth.items()))
    print(f"    {'config':22s} " + "".join(f"{c:>26s}" for c in CATS))
    for name, d in CONFIGS:
        p = Path(d) / f"{stem}.json"
        if not p.exists():
            continue
        runs = json.load(open(p))
        cells = []
        for c in CATS:
            dist = Counter(counts(r)[c] for r in runs)
            cells.append(f"{fmt(dist, truth.get(c)):>26s}")
        print(f"    {name:22s} " + "".join(cells))
    if truth:
        print(f"    {'':22s} " + "".join(f"{'':>26s}" for _ in CATS))
        for name, d in CONFIGS:
            p = Path(d) / f"{stem}.json"
            if not p.exists(): continue
            runs = json.load(open(p))
            hits = sum(1 for r in runs if all(counts(r)[c] == truth[c] for c in CATS))
            near = sum(1 for r in runs
                       if sum(1 for c in CATS if counts(r)[c] == truth[c]) >= len(CATS) - 1)
            print(f"    {name:22s} all 5 categories right: {hits:2d}/{len(runs)}"
                  f"   4 of 5 right: {near:2d}/{len(runs)}")
print("\n(* marks the hand-checked correct count)")
