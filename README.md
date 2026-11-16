# Group interactions in the data, in the best model, or in the system

Code, results and source for the Perspective "Group interactions in the data, in the best
model, or in the system" by Leo Torres, written for the Frontiers in Complex Systems
Research Topic "Higher Order versus Pairwise Interactions: A Modeling Debate".

## Contents

- `study/`: the simulated benchmark. People meet in gatherings and adopt a behavior by a
  pairwise mechanism, a group mechanism or a mix. The gatherings are recorded as a
  meeting log and by proximity sensors. Graph and hypergraph models are fitted to each
  record and compared by message length and by held-out misfit, and their predictions
  of the effect of meeting adopters together rather than one at a time are compared with
  the true effect. `study/SIMULATION.md` is the full specification (Supplementary File
  S1) and `study/supplement.md` compares three ways of holding out data (File S2).
  Results of every run are in `study/outputs/runs/`.
- `remedy/`: an independent check, written from `study/SIMULATION.md` alone, of a model
  with a separate rate for two or more adopters (Supplementary File S3,
  `remedy/SUPPLEMENT.md`).
- `paper/`: the source of the Perspective in RSM (`perspective.rsm`), its figures, and the
  supplementary files as PDFs (`paper/supplement/`).

## Reproducing the results

The code uses [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/).

```
cd study
just test             # tests
just tune             # tune the main setting (writes outputs/tuned/)
just run pilot        # the 20 runs of the main setting
just sweep            # the other 13 settings
just report pilot     # tables for one setting, or "sweep" for all
just figure           # Figures 1 and 2 and the figure of File S2

cd ../remedy
just run              # the independent check behind File S3

cd ../paper
just build            # the HTML page (needs RSM)
just supplement       # Files S1 to S3 as PDFs (needs pandoc and xelatex)
```

Runs that already have a result file are skipped, so delete or move `study/outputs/runs/`
to recompute them.

## License

MIT, see `LICENSE`.
