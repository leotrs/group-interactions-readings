"""Set the world's free numbers (spec.md) and write them to
outputs/tuned/partners_X.json.

1. Gathering rate: each person is with about X distinct people a day (pilot: 6).
2. Seeds: with mu = 1/900 s fixed, the number of initial adopters at which about half
   of people adopt under the joint mechanism.
3. lam: with the same seeds, the rate at which about half adopt under the independent
   mechanism. The "both" mechanism then uses lam/2 and mu/2 (world.rate).

Usage: uv run python tune.py [PARTNERS_PER_DAY]   (default: the pilot value)
"""

import sys
from dataclasses import asdict, replace

import world
from common import PILOT, tuned_path, write_json

RUNS = 30
TARGET = 0.5


def main(partners):
    p = world.Params()
    rate = world.calibrate_gathering_rate(p, target=partners)
    p = replace(p, gathering_rate=rate)
    print("gathering rate per day", p.gathering_rate * world.DAY, flush=True)

    seeds = None
    for s in range(2, 101):
        frac = world.adoption_fraction(replace(p, n_seeds=s), "joint", RUNS, seed=1)
        print("seeds", s, "joint adoption", round(frac, 3), flush=True)
        if frac >= TARGET:
            seeds = s
            break
    if seeds is None:
        raise RuntimeError("joint mechanism never reached half adoption")
    p = replace(p, n_seeds=seeds)

    lo, hi = 1e-7, 1e-2
    for _ in range(25):
        mid = (lo * hi) ** 0.5
        frac = world.adoption_fraction(replace(p, lam=mid), "independent", RUNS, seed=2)
        lo, hi = (mid, hi) if frac < TARGET else (lo, mid)
    p = replace(p, lam=(lo * hi) ** 0.5)

    fractions = {m: world.adoption_fraction(p, m, RUNS, seed=3)
                 for m in world.MECHANISMS}
    print("adoption fractions", fractions, flush=True)
    write_json(tuned_path({"partners_per_day": partners}),
               {"params": asdict(p), "fractions": fractions})


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else PILOT["partners_per_day"])
