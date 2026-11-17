"""Check that the code reproduces the saved results.

Usage: uv run python verify.py [SETTING:RUN ...]
Recomputes the tuning of the main setting and the given runs (default: two runs of the
main setting and one of the sweep) and compares them with the saved files.

On the machine that made the results (Apple M-series, macOS) every number comes out
identical, and the check says so. On other processors the maximum-likelihood fits stop
at slightly different points: fitted parameters can differ by about one part in 10,000,
the size of the optimizer's stopping tolerance. The check then asks whether the
results of the paper are reproduced: in every world and record, the same model must
win under every criterion, and every predicted effect must be within EFFECT_TOL
percentage points. It also prints the largest relative difference among all numbers.
Exits with an error if a result of the paper is not reproduced.
"""

import json
import sys

import run
import tune
from models import CHECK_MODELS, MODELS
from results import CRITERIA, criterion_bits, effect, winner
from settings import settings, tuned_path

DEFAULT = ["main:0", "main:7", "detection_probability=0.25:3"]
EFFECT_TOL = 0.1  # percentage points


def largest_difference(a, b, path=""):
    """(relative difference, where) for the number that differs most."""
    if isinstance(a, dict):
        return max((largest_difference(a[k], b[k], f"{path}/{k}") for k in a),
                   default=(0.0, path))
    if isinstance(a, list):
        return max((largest_difference(x, y, f"{path}/{i}")
                    for i, (x, y) in enumerate(zip(a, b))), default=(0.0, path))
    if isinstance(a, (int, float)) and a != b:
        return abs(a - b) / max(abs(a), abs(b)), path
    return 0.0, path


def paper_results_differ(new, saved):
    """Descriptions of every winner or predicted effect that differs."""
    out = []
    for cn, cs in zip(new["conditions"], saved["conditions"]):
        where = f"{cn['world']}, {cn['record']}"
        for criterion in CRITERIA:
            wn, ws = (winner({m: criterion_bits(criterion, c["models"][m])
                              for m in MODELS}) for c in (cn, cs))
            if wn != ws:
                out.append(f"{where}: winner by {criterion} is {wn}, saved {ws}")
        for group, ms in (("models", MODELS), ("check_models", CHECK_MODELS)):
            for m in ms:
                en, es = (effect(c[group][m]["together_apart"]) for c in (cn, cs))
                if abs(en - es) > EFFECT_TOL:
                    out.append(f"{where}: effect predicted by {m} is {en:.2f}, "
                               f"saved {es:.2f}")
    return out


def check(label, new, saved, has_conditions=True):
    new = json.loads(json.dumps(new))
    if new == saved:
        print(f"{label}: identical")
        return True
    rel, where = largest_difference(new, saved)
    problems = (paper_results_differ(new, saved) if has_conditions
                else ["the tuning differs"])
    status = ("results of the paper DIFFER" if problems
              else "results of the paper reproduced")
    print(f"{label}: {status} (largest relative difference {rel:.1e} at {where})")
    for p in problems:
        print("   ", p)
    return not problems


def main(targets):
    saved = json.loads(tuned_path(settings("main")).read_text())
    ok = check("tuning of the main setting",
               tune.tuned_params(settings("main")["people_met_per_day"]), saved,
               has_conditions=False)
    for target in targets:
        name, r = target.rsplit(":", 1)
        saved = json.loads(run.run_path(name, int(r)).read_text())
        ok &= check(f"{name}, run {r}", run.compute_run(name, int(r)), saved)
    sys.exit(0 if ok else "the code does not reproduce the saved results")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)
