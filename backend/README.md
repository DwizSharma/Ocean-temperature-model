# OceanEmbed backend

OceanEmbed reconstructs a 23-depth subsurface ocean-temperature profile from global satellite observations: SST (sea-surface temperature) and SSH/SLA (sea-surface height / sea-level anomaly). This repository is **backend only**: it exposes a FastAPI REST API for a separate frontend.

The frontend sends a latitude, longitude, and target month. It never sends SST, SSH, or ARGO. The backend loads the three global satellite grids needed by the configured ConvLSTM, predicts a `180 x 360 x 23` global temperature field, and returns the profile at the nearest 1-degree grid cell.

ARGO is deliberately not an inference input. It is ground truth used during training and validation.

## Current prototype limitation

`prototype-v1` was trained only with January, February, and March 2020 and predicts March 2020. Its default configuration accepts **only `2020-03`**. It is not a general ocean-temperature model. A future model trained over many rolling windows can support more months without changing the API: update the model path/version, preprocessing artifact, temporal window, and supported-month setting in `.env`.

## Architecture

```text
POST /api/v1/predict (latitude, longitude, target_month)
  -> PredictionService
     -> TemporalService: target month -> required monthly inputs
     -> SSTRepository + SSHRepository: load and align global NetCDF grids
     -> Preprocessor: fill NaNs with saved training means and normalize
     -> ModelService: one global ConvLSTM inference
     -> LocationService: nearest grid cell -> 23-depth profile
```

The model sees `(1, 3, 180, 360, 2)`, not latitude or longitude. Channels are always `[SST, SSH/SLA]`. Coordinates are used only after the global prediction is produced.

## Project layout

```text
app/                         FastAPI routes, schemas, services, repositories
model/                       Place the .keras file here by default
data/SST/                    Place SST_YYYYMM_*.nc files here
data/SSH/                    Place SSH_YYYYMM_*.nc files here
preprocessing_artifacts/     Place training-derived preprocessing_stats.npz here
tests/                       Fast unit and integration-style tests using fakes
```

## Install and configure

Use Python 3.10 or 3.11 (a TensorFlow-compatible version).

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` if using other paths, for example the Google Drive paths from the training notebook:

```env
MODEL_PATH=/content/drive/MyDrive/SIH2026/Models/ConvLSTM_JanFebMar_Prototype.keras
SST_DATA_DIR=/content/drive/MyDrive/SIH2026/Dataset/OISST_Monthly
SSH_DATA_DIR=/content/drive/MyDrive/SIH2026/Dataset/SSH_Monthly
PREPROCESSING_STATS_PATH=/content/drive/MyDrive/SIH2026/preprocessing_stats.npz
MODEL_VERSION=prototype-v1
TEMPORAL_WINDOW_MONTHS=3
SUPPORTED_TARGET_MONTHS=2020-03
ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173
```

Alternatively, copy the model into `model/`, files such as `SST_202001_1deg.nc` into `data/SST/`, and `SSH_202001_1deg.nc` into `data/SSH/`. Filenames must begin with `SST_YYYYMM` and `SSH_YYYYMM`; their NetCDF variables can use common names such as `sst`, `analysed_sst`, `sla`, or `ssh`.

### Preprocessing artifact (required)

Create `preprocessing_artifacts/preprocessing_stats.npz` from the **same training preprocessing run**. It must contain scalar `sst_mean`, `sst_std`, `ssh_mean`, and `ssh_std`. Do not calculate replacement values per API request and do not guess them: the values must match training. A small safe example command, to run with your real saved values, is:

```python
import numpy as np
np.savez("preprocessing_artifacts/preprocessing_stats.npz",
         sst_mean=YOUR_SST_MEAN, sst_std=YOUR_SST_STD,
         ssh_mean=YOUR_SSH_MEAN, ssh_std=YOUR_SSH_STD)
```

Large model/data artifacts are ignored by Git on purpose. The server loads the model and stats once at startup, not once per request.

## Run the API

```bash
uvicorn app.main:app --reload
```

Swagger is at `http://127.0.0.1:8000/docs`; ReDoc is at `/redoc`. Check startup state at `GET /health`. If the model or preprocessing artifact is missing, health reports `unhealthy` and predictions are unavailable without exposing server paths.

## Frontend API contract

The contract is intentionally stable across model replacements.

```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict \
  -H 'Content-Type: application/json' \
  -d '{"latitude":20.5,"longitude":75.5,"target_month":"2020-03"}'
```

The response has this shape (the temperature values are model outputs, not fixed example values):

```json
{
  "latitude": 20.5,
  "longitude": 75.5,
  "grid_latitude": 20.5,
  "grid_longitude": 75.5,
  "target_month": "2020-03",
  "depths_m": [30, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1750, 2000],
  "temperature_celsius": ["23 model-generated numbers"],
  "model_version": "prototype-v1"
}
```

Latitude must be from -90 to 90. Longitude accepts `-180..180` or `0..360` and is returned normalized to `0..360`. The API chooses the nearest centers on the latitude `-89.5..89.5` and longitude `0.5..359.5` grid. Invalid requests produce FastAPI 422 responses. Missing satellite inputs, land/no-data cells, and unavailable services return clear safe errors.

`GET /api/v1/model-info` advertises the stable tensor metadata but never exposes filesystem paths.

## Temporal windows and replacing the model

With the prototype's `TEMPORAL_WINDOW_MONTHS=3`, a `2020-03` target requires `2020-01`, `2020-02`, `2020-03`. This logic belongs exclusively to `TemporalService`.

After training `OceanEmbed_v2.keras`, replace the artifact and update `.env`, for example:

```env
MODEL_PATH=model/OceanEmbed_v2.keras
MODEL_VERSION=oceanembed-v2
TEMPORAL_WINDOW_MONTHS=6
SUPPORTED_TARGET_MONTHS=
PREPROCESSING_STATS_PATH=preprocessing_artifacts/v2_stats.npz
```

Only do this when the future model actually accepts a six-month `(time, 180, 360, 2)` input and emits the same 23-depth global output. If its tensor contract changes, adapt `ModelService`/configuration while keeping `POST /api/v1/predict` and its response schema unchanged.

## Tests

```bash
pytest
```

Tests cover health, model information, request validation, longitude behavior, temporal arithmetic, nearest-grid selection, response depth count, and a complete mocked orchestration flow. They do not require TensorFlow, real NetCDF data, or a real `.keras` artifact.
