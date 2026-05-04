# Notebooks

Reproducibility notebooks executed via `papermill`. Naming convention
`<phase><index>-<topic>.ipynb`, e.g. `B2-hcf-construction.ipynb`.

`make repro` regenerates every figure in `paper/figures/` from these
notebooks against DVC-pinned datasets.
