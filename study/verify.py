"""Check that the code reproduces the saved results.

Usage: uv run python verify.py [SETTING:RUN ...]
Recomputes the tuning of the main setting and the given runs (default: two runs of the
main setting and one of the sweep), and compares every number with the saved files.

On the machine that made the results (Apple M-series, macOS) every number comes out
identical. On other processors the fits can differ in the last digits, so a number
counts as reproduced if it is within RTOL of the saved one; the largest difference
found is printed. Exits with an error if any number differs by more.
"""

import json
import sys

import run
import tune
from settings import settings, tuned_path

DEFAULT = ["main:0", "main:7", "detection_probability=0.25:3"]
RTOL = 1e-9


def differences(a, b, path=""):
    """Relative differences between two results, after the JSON round trip that the
    saved files went through; inf where the structure or a non-number differs."""
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return [(path, float("inf"))]
        return [d for k in a for d in differences(a[k], b[k], f"{path}/{k}")]
    if isinstance(a, list):
        if len(a) != len(b):
            return [(path, float("inf"))]
        return [d for i, (x, y) in enumerate(zip(a, b))
                for d in differences(x, y, f"{path}/{i}")]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if a == b:
            return [(path, 0.0)]
        return [(path, abs(a - b) / max(abs(a), abs(b)))]
    return [(path, 0.0 if a == b else float("inf"))]


def check(label, new, saved):
    diffs = differences(json.loads(json.dumps(new)), saved)
    worst_path, worst = max(diffs, key=lambda d: d[1])
    if worst == 0:
        print(f"{label}: identical ({len(diffs)} values)")
    elif worst <= RTOL:
        print(f"{label}: reproduced ({len(diffs)} values, largest relative difference "
              f"{worst:.1e} at {worst_path})")
    else:
        print(f"{label}: DIFFERS (relative difference {worst:.1e} at {worst_path})")
    return worst <= RTOL


def main(targets):
    saved = json.loads(tuned_path(settings("main")).read_text())
    ok = check("tuning of the main setting",
               tune.tuned_params(settings("main")["people_met_per_day"]), saved)
    for target in targets:
        name, r = target.rsplit(":", 1)
        saved = json.loads(run.run_path(name, int(r)).read_text())
        ok &= check(f"{name}, run {r}", run.compute_run(name, int(r)), saved)
    sys.exit(0 if ok else "the code does not reproduce the saved results")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)
