# External API Landslide Model

## Purpose

This model uses external environmental and seismic API features to classify
landslide inventory points versus pseudo-background points.

## Integrated APIs

- NASA POWER Daily API: rainfall, temperature, humidity, and wind lookback
  features before the event date.
- USGS Earthquake Catalog API: earthquake count, maximum magnitude, nearest
  earthquake distance, and magnitude-distance score before the event date.
- OpenWeather One Call 3.0 Daily Aggregation: optional historical weather
  features when `OPENWEATHER_API_KEY` is available.

## Current Training Run

The current model was trained on a deliberately small live API sample to keep
API usage modest:

- 50 landslide inventory samples
- 50 pseudo-background samples
- 100 total rows
- NASA POWER and USGS features populated
- OpenWeather code integrated but not used in this run because no API key was
  available in the environment

## Validation Metrics

From `reports/external_api_model_metrics.json`:

- Test ROC-AUC: 0.683
- Test average precision: 0.502
- Best-F1 threshold: 0.352
- Best-F1 precision: 0.500
- Best-F1 recall: 1.000
- Best-F1 F1: 0.667

These metrics are from a very small spatial split and should be treated as a
pipeline validation result, not as final scientific model performance.

## Outputs

- `data/features/api_training_points.csv`
- `models/external_api_landslide_model.json`
- `reports/external_api_model_metrics.json`
- `reports/external_api_predictions.csv`

## Recommended Next Step

Scale the training table gradually, for example 500 positives plus 500
background samples, then 2,000 plus 2,000 if API throughput and cache behavior
look healthy. Keep spatial validation enabled and compare this model against
the coordinate-only baseline.
