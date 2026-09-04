# Required training artifact

Place `preprocessing_stats.npz` in this directory (or point `PREPROCESSING_STATS_PATH` at it).

It must be exported from the model's training preprocessing with four scalar keys:

- `sst_mean`
- `sst_std`
- `ssh_mean`
- `ssh_std`

This repository deliberately does not include invented values. Inference must use exactly the statistics used to train the `.keras` model.
