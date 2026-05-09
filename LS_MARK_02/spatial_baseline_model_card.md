# Spatial Baseline Landslide Model

## Purpose

This model estimates a `landslide_susceptibility` score for latitude/longitude
points in and around the India landslide inventory coverage area.

## Model Type

Coordinate-only spatial RBF logistic baseline.

The model uses:

- Historic landslide inventory points as positive samples.
- Randomly sampled pseudo-background points as negative samples.
- Latitude/longitude transformed into local kilometer coordinates.
- Radial-basis spatial features centered on historic landslide clusters.

## Training Data

- Positive inventory points after coordinate deduplication: 31,629
- Pseudo-background points: 31,629
- Total training/evaluation points: 63,258

## Validation

Validation uses a spatial block split with 1-degree blocks, so nearby points are
less likely to leak between train and test sets.

Metrics from `reports/spatial_baseline_metrics.json`:

- Test ROC-AUC: 0.900
- Test average precision: 0.921
- Best-F1 test threshold: 0.00421
- Best-F1 test precision: 0.815
- Best-F1 test recall: 0.999
- Best-F1 test F1: 0.898

## Outputs

- `models/spatial_baseline_model.json`
- `reports/spatial_baseline_metrics.json`
- `reports/spatial_baseline_susceptibility_grid.csv`
- `reports/spatial_baseline_top_grid_points.csv`
- `data/features/spatial_baseline_training_points.csv`

## Important Limitations

This is not yet a full physical landslide prediction model. It is a spatial
susceptibility prior based on where historic landslides were recorded. It may
learn inventory density, reporting bias, road-survey bias, and state-wise data
coverage rather than physical landslide causality.

For a stronger model, add terrain, rainfall, geology, land-cover, drainage,
road-distance, river-distance, and fault-distance features, then retrain with
spatial or regional holdout validation.
