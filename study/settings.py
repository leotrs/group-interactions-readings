"""The settings of the study: the main setting, the sweep, and where results are kept.

A setting is a value for each of six hyperparameters. The main setting is the one
reported in the paper; the sweep changes one hyperparameter at a time from it (Figure
1E). A setting is named "main" or "hyperparameter=value", for example
"detection_probability=0.25".
"""

import hashlib
import json
import os
from pathlib import Path

OUTPUTS = Path(os.environ.get("STUDY_OUTPUTS", Path(__file__).parent / "outputs"))

MAIN = {
    "people_met_per_day": 6.0,     # distinct people each person meets a day, on average
    "detection_probability": 0.5,  # chance that a sensor sample detects a pair
    "sampling_interval": 20.0,     # seconds between sensor samples
    "adoption_delay": 0.0,         # mean delay in recorded adoption times, in seconds
    "processes_fitted": 1,         # spreading processes fitted (and as many held out)
    "sensor_groups": "components",  # "components" of detected pairs, or "gatherings"
}

SWEEP = {
    "people_met_per_day": [3.0, 10.0, 25.0],
    "detection_probability": [0.25, 0.75, 1.0],
    "sampling_interval": [60.0, 300.0],
    "adoption_delay": [300.0, 1800.0],
    "processes_fitted": [5, 10],
    "sensor_groups": ["gatherings"],
}

RUNS = 20         # runs per setting; run r uses random seed r
EXPOSURE = 900.0  # seconds of each meeting in the together-or-one-at-a-time question


def settings(name):
    """The hyperparameter values of the setting called `name`."""
    s = dict(MAIN)
    if name != "main":
        key, value = name.split("=")
        s[key] = value if key == "sensor_groups" else type(MAIN[key])(value)
    return s


def setting_names():
    return ["main"] + [f"{k}={v}" for k, vs in SWEEP.items() for v in vs]


def tuned_path(s):
    """The world's tuned rates depend only on how many people each person meets."""
    return OUTPUTS / "tuned" / f"people_met_per_day={s['people_met_per_day']}.json"


def run_path(name, run):
    return OUTPUTS / "runs" / name / f"run_{run:02d}.json"


def write_json(path, obj):
    """Write to a temporary file, then rename, so a crash never leaves half a file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    tmp.replace(path)


def fingerprint(path):
    """A short hash of a file, stored with each run to tie it to its tuning."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
