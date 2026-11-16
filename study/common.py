"""Paths, pilot settings, and safe writing of results."""

import hashlib
import json
import os
from pathlib import Path

OUTPUTS = Path(os.environ.get("HOI_OUTPUTS", Path(__file__).parent / "outputs"))

# Pilot values of the hyperparameters (spec.md; values approved 2026-11-13). Both
# structure codes are computed in every run, so the code is not a setting.
PILOT = {"partners_per_day": 6.0, "d": 0.5, "interval": 20.0, "delta": 0.0,
         "processes": 1, "grouping": "parts"}

# The sweep changes one setting at a time from the pilot values.
SWEEP = {"partners_per_day": [3.0, 10.0, 25.0], "d": [0.25, 0.75, 1.0],
         "interval": [60.0, 300.0], "delta": [300.0, 1800.0], "processes": [5, 10],
         "grouping": ["gathering"]}


def settings(name):
    """'pilot', or one change from it written as key=value, e.g. 'd=0.25'."""
    s = dict(PILOT)
    if name != "pilot":
        key, value = name.split("=")
        s[key] = type(PILOT[key])(value) if key != "grouping" else value
    return s


def setting_names():
    return ["pilot"] + [f"{k}={v}" for k, vs in SWEEP.items() for v in vs]


def tuned_path(s):
    return OUTPUTS / "tuned" / f"partners_{s['partners_per_day']}.json"


REPLICATES = 20
EXPOSURE = 900.0  # length of each meeting in the together-vs-apart experiment


def write_json(path, obj):
    """Write to a temporary file, then rename, so a crash never leaves half a file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    tmp.replace(path)


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
