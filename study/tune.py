"""Tune the world's free rates for a number of people met per day.

Usage: uv run python tune.py [PEOPLE_MET_PER_DAY]   (default: the main setting, 6)
Writes outputs/tuned/people_met_per_day=X.json. In this order:

1. Gathering rate: each person meets X distinct people a day on average.
2. First adopters: with mu = 1/900 per second fixed, the smallest number, counting up
   from 2, at which at least half of the people adopt in the group world.
3. lam: with those first adopters, the rate at which half of the people adopt in the
   pairwise world, found by bisection on a log scale. The mixed world then uses lam / 2
   and mu / 2 (world.rate).

Each check averages 30 events. Every step uses its own fixed random seed, so the result
is the same on every machine that has the same versions of the libraries.
"""

import sys
from dataclasses import asdict, replace

import world
from settings import MAIN, tuned_path, write_json

EVENTS = 30
TARGET = 0.5


def tuned_params(people_met):
    """The tuned parameters and the resulting adoption fractions, as saved."""
    p = world.Params()
    p = replace(p, gathering_rate=world.calibrate_gathering_rate(p, target=people_met))
    print("gatherings per day", p.gathering_rate * world.DAY, flush=True)

    for n in range(2, 101):
        frac = world.adoption_fraction(replace(p, n_first_adopters=n), "group", EVENTS,
                                       seed=1)
        print("first adopters", n, "adoption in the group world", round(frac, 3),
              flush=True)
        if frac >= TARGET:
            break
    else:
        raise RuntimeError("the group world never reached half adoption")
    p = replace(p, n_first_adopters=n)

    lo, hi = 1e-7, 1e-2
    for _ in range(25):
        mid = (lo * hi) ** 0.5
        frac = world.adoption_fraction(replace(p, lam=mid), "pairwise", EVENTS, seed=2)
        lo, hi = (mid, hi) if frac < TARGET else (lo, mid)
    p = replace(p, lam=(lo * hi) ** 0.5)

    fractions = {w: world.adoption_fraction(p, w, EVENTS, seed=3) for w in world.WORLDS}
    print("adoption fractions", fractions, flush=True)
    return {"params": asdict(p), "adoption_fractions": fractions}


def main(people_met):
    write_json(tuned_path({"people_met_per_day": people_met}), tuned_params(people_met))


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else MAIN["people_met_per_day"])
