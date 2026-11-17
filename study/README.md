# The simulated benchmark

This folder holds the code, the saved results and the figures of the simulated study
in Section 3 of the paper. The full specification of the study is
[SIMULATION.md](SIMULATION.md) (Supplementary File S1); this page explains the code.

## What the study does

Two hundred people attend a three-day event and meet in gatherings. A behavior spreads
among them in one of three worlds: pairwise, group or mixed. The gatherings are recorded
in two ways: a meeting log and proximity sensors. Three models (a linear graph model, a
nonlinear graph model and a hypergraph model) are fitted to each record and compared by
message length and by held-out misfit. Each fitted model also predicts how much more
likely a person is to adopt after meeting two adopters together rather than one at a
time, and the prediction is compared with the true effect. A fourth model, the linear
graph model with an added group rate, is fitted for that prediction only.

## Where each part of the paper comes from

| Paper | Code | Output |
|---|---|---|
| Event, worlds, spreading (Section 3.1) | `world.py`, `tune.py` | `outputs/tuned/` |
| Records (Section 3.1, Figure 1B) | `records.py` | |
| Models, fitting, causal effect (Figure 1C) | `models.py` | |
| Bits for writing down the record (Figure 1D) | `codes.py` | |
| Hyperparameters, main setting, sweep (Figure 1E) | `settings.py` | |
| Runs | `run.py` | `outputs/runs/SETTING/run_RR.json` |
| Numbers in Section 3.2 | `results.py`, `report.py` | printed by `just report` |
| Figure 1 | `design_figure.py` | `outputs/figures/figure1.*` |
| Figure 2 and the figure of File S2 | `figures.py` | `outputs/figures/figure2.*`, `figure_s2.*` |
| Supplementary File S2 | [supplement.md](supplement.md) | |

`style.py` holds the colors and the figure style shared by the figures.
[empirical_values.md](empirical_values.md) collects the published measurements that the
hyperparameters were checked against, with quotes and page numbers.

## Running it

The code uses [uv](https://docs.astral.sh/uv/) for Python and its libraries, and
[just](https://just.systems/) for the commands below. `uv` installs Python 3.15 and the
exact library versions in `uv.lock` on first use.

```
just test       # unit tests (about 10 s)
just verify     # recompute the tuning and three runs, check them against the saved files
just report     # the numbers of the main setting; `just report sweep` for all settings
just figures    # Figures 1 and 2 and the figure of File S2, from the saved runs
just all        # everything from scratch: tuning, all 14 settings x 20 runs, report and
                # figures (about an hour with 3 processes)
```

`just run SETTING` runs a single setting; finished runs are skipped, so an interrupted
job resumes where it stopped. To recompute runs that already exist, move
`outputs/runs/` away first, or set `STUDY_OUTPUTS` to another folder.

## Reproducibility

- Every random draw comes from a fixed seed. Tuning uses seeds 0 to 3, one per step
  (`tune.py`). Run r of every setting uses seed r, and draws in a fixed order: the
  gatherings, a random half of the people, the sensor record, then the spreading
  processes of each world in turn (`run.py`).
- With the library versions in `uv.lock` (numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2,
  Python 3.15), the code gives exactly the saved results; `just verify` checks this.
  Other versions of numpy can change the random streams, and other versions of scipy
  can change the fits in the last digits.
- Each run file stores a hash of the tuning file that it was made from, and the report
  refuses to mix runs made from different tunings.

## Results files

A run file has one entry per world and record (`conditions`). For each of the three
compared models it stores the fitted parameters (`params`: lam, b and nu), the bits for
writing down the record (`structure_bits`, and `structure_bits_cliques` for the clique
code), the bits for the rule (`rule_bits`), the held-out misfit (`heldout_misfit_bits`),
the misfits under the two other ways of holding out data, and the predicted chances of
adopting together and one at a time (`together_apart`). The message length of the paper
is `structure_bits + rule_bits + heldout_misfit_bits`. The model with a group rate is
stored under `check_models`; its parameters are lam, b and mu.
