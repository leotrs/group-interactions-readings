# Group interactions in the data, in the best model, or in the system

Code, results and source of the Perspective "Group interactions in the data, in the
best model, or in the system" by Leo Torres, written for the Frontiers in Complex
Systems Research Topic "Higher order versus pairwise interactions: A modeling debate".

The paper distinguishes three readings of the claim that a system has group
interactions: about how the data were recorded, about which model predicts them best,
and about how the system works. A simulated benchmark shows that comparing graph and
hypergraph models on recorded data supports only the second reading. This repository
holds that benchmark, an independent check of one of its results, and the paper.

## Contents

| Folder | What it holds | Start with |
|---|---|---|
| [`study/`](study/) | The simulated benchmark: code, the saved results of every run, Figures 1 and 2, Supplementary Files S1 and S2 | [study/README.md](study/README.md) |
| [`independent_check/`](independent_check/) | A separate implementation, written from File S1 alone, of the model with a group rate (Supplementary File S3) | [independent_check/README.md](independent_check/README.md) |
| [`paper/`](paper/) | The paper's source (`perspective.rsm`), its Frontiers LaTeX version and PDF, and the supplementary files as PDFs | `paper/frontiers/torres_perspective.pdf` |

## Reproducing the results

Requirements: [uv](https://docs.astral.sh/uv/) and [just](https://just.systems/). uv
installs Python 3.15 and the exact library versions in each folder's `uv.lock`.

```
cd study
just test        # unit tests, about 10 s
just verify      # recompute the tuning and three runs; compare with the saved results
just report      # the numbers reported in the paper (main setting)
just figures     # Figures 1 and 2 and the figure of File S2, from the saved runs
just all         # everything from scratch, about an hour with 3 processes

cd ../independent_check
just run         # the 20 runs behind File S3, about 10 s
just verify      # rerun them and check that the results file comes out identical

cd ../paper
just build       # the web version (needs RSM)
just latex       # the Frontiers LaTeX version and its PDF (needs pdflatex)
just supplement  # Supplementary Files S1 to S3 as PDFs (needs pandoc and xelatex)
```

Every random draw comes from a fixed seed, so the code gives the saved results exactly
with the locked library versions on the machine that made them (Apple M-series,
macOS). On other processors, the fits can differ in the last digits; `just verify`
reports the largest difference. The tests and `just verify` run on every push
(`.github/workflows/tests.yml`).

## Citation

See [CITATION.cff](CITATION.cff).

## License

MIT, see [LICENSE](LICENSE).
