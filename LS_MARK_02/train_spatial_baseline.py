#!/usr/bin/env python3
"""Train a baseline landslide susceptibility model from the inventory.

This is a spatial baseline, not a full physical landslide model. It uses known
landslide points as positives and sampled pseudo-background points as negatives.
The score should be read as "similarity to historic inventory locations" until
terrain, rainfall, geology, and land-cover covariates are added.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from spatial_baseline_lib import (
    average_precision_score,
    best_f1_threshold_metrics,
    binary_metrics,
    choose_rbf_sigma,
    kmeans_centers,
    latlon_to_xy,
    make_features,
    predict_scores,
    roc_auc_score,
    sample_background_points,
    save_json,
    spatial_train_test_split,
    train_logistic_regression,
    write_prediction_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        default=Path("data/processed/landslide_inventory.csv"),
        type=Path,
        help="Extracted landslide inventory CSV.",
    )
    parser.add_argument(
        "--model-out",
        default=Path("models/spatial_baseline_model.json"),
        type=Path,
        help="Path to write the trained JSON model.",
    )
    parser.add_argument(
        "--metrics-out",
        default=Path("reports/spatial_baseline_metrics.json"),
        type=Path,
        help="Path to write model metrics.",
    )
    parser.add_argument(
        "--training-out",
        default=Path("data/features/spatial_baseline_training_points.csv"),
        type=Path,
        help="Path to write generated positive/background training points.",
    )
    parser.add_argument(
        "--grid-out",
        default=Path("reports/spatial_baseline_susceptibility_grid.csv"),
        type=Path,
        help="Path to write a coarse prediction grid.",
    )
    parser.add_argument(
        "--eval-out",
        default=Path("reports/spatial_baseline_eval_predictions.csv"),
        type=Path,
        help="Path to write train/test row-level predictions.",
    )
    parser.add_argument("--background-ratio", default=1.0, type=float)
    parser.add_argument("--background-buffer-degrees", default=0.5, type=float)
    parser.add_argument("--background-min-distance-km", default=5.0, type=float)
    parser.add_argument("--block-degrees", default=1.0, type=float)
    parser.add_argument("--test-fraction", default=0.25, type=float)
    parser.add_argument("--rbf-centers", default=96, type=int)
    parser.add_argument("--kmeans-iterations", default=25, type=int)
    parser.add_argument("--epochs", default=60, type=int)
    parser.add_argument("--batch-size", default=4096, type=int)
    parser.add_argument("--learning-rate", default=0.015, type=float)
    parser.add_argument("--l2", default=0.0005, type=float)
    parser.add_argument("--grid-step-degrees", default=0.25, type=float)
    parser.add_argument("--seed", default=42, type=int)
    return parser.parse_args()


def load_positive_points(inventory_path: Path) -> pd.DataFrame:
    df = pd.read_csv(inventory_path)
    required = {"latitude", "longitude"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Inventory is missing columns: {sorted(missing)}")

    points = df.dropna(subset=["latitude", "longitude"]).copy()
    points = points[
        points["latitude"].between(6.0, 38.0)
        & points["longitude"].between(68.0, 98.5)
    ]
    points = points.drop_duplicates(["latitude", "longitude"])
    points["label"] = 1
    return points


def make_prediction_grid(
    positive_latlon: np.ndarray,
    buffer_degrees: float,
    step_degrees: float,
) -> np.ndarray:
    latitudes = np.arange(
        positive_latlon[:, 0].min() - buffer_degrees,
        positive_latlon[:, 0].max() + buffer_degrees + step_degrees,
        step_degrees,
    )
    longitudes = np.arange(
        positive_latlon[:, 1].min() - buffer_degrees,
        positive_latlon[:, 1].max() + buffer_degrees + step_degrees,
        step_degrees,
    )
    lon_grid, lat_grid = np.meshgrid(longitudes, latitudes)
    return np.column_stack([lat_grid.ravel(), lon_grid.ravel()])


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)

    positives = load_positive_points(args.inventory)
    positive_latlon = positives[["latitude", "longitude"]].to_numpy(dtype=float)
    background_count = int(round(len(positive_latlon) * args.background_ratio))
    background_latlon = sample_background_points(
        positive_latlon=positive_latlon,
        count=background_count,
        rng=rng,
        buffer_degrees=args.background_buffer_degrees,
        min_distance_km=args.background_min_distance_km,
    )

    positive_frame = positives[["latitude", "longitude", "label"]].copy()
    positive_frame["sample_type"] = "inventory_positive"
    background_frame = pd.DataFrame(
        {
            "latitude": background_latlon[:, 0],
            "longitude": background_latlon[:, 1],
            "label": 0,
            "sample_type": "pseudo_background",
        }
    )
    training_points = pd.concat([positive_frame, background_frame], ignore_index=True)
    training_points = training_points.sample(frac=1.0, random_state=args.seed).reset_index(
        drop=True
    )
    args.training_out.parent.mkdir(parents=True, exist_ok=True)
    training_points.to_csv(args.training_out, index=False)

    latlon = training_points[["latitude", "longitude"]].to_numpy(dtype=float)
    labels = training_points["label"].to_numpy(dtype=float)
    train_idx, test_idx = spatial_train_test_split(
        latlon,
        labels,
        rng=rng,
        block_degrees=args.block_degrees,
        test_fraction=args.test_fraction,
    )

    origin_lat = float(latlon[:, 0].min())
    origin_lon = float(latlon[:, 1].min())
    reference_lat = float(latlon[:, 0].mean())
    train_positive_latlon = latlon[train_idx][labels[train_idx] == 1]
    train_positive_xy = latlon_to_xy(
        train_positive_latlon[:, 0],
        train_positive_latlon[:, 1],
        origin_lat,
        origin_lon,
        reference_lat,
    )
    centers = kmeans_centers(
        train_positive_xy,
        center_count=args.rbf_centers,
        rng=rng,
        iterations=args.kmeans_iterations,
    )

    params = {
        "origin_latitude": origin_lat,
        "origin_longitude": origin_lon,
        "reference_latitude": reference_lat,
        "centers_xy": centers.tolist(),
        "rbf_sigma_km": choose_rbf_sigma(centers),
        "feature_mean": [],
        "feature_std": [],
    }

    X_train, params = make_features(latlon[train_idx], params, fit_scaler=True)
    X_test, _ = make_features(latlon[test_idx], params, fit_scaler=False)
    y_train = labels[train_idx]
    y_test = labels[test_idx]

    weights, bias, losses = train_logistic_regression(
        X_train,
        y_train,
        rng=rng,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        l2=args.l2,
    )

    model = {
        "model_type": "spatial_rbf_logistic_baseline",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "warning": (
            "Baseline trained with pseudo-background points and coordinate-only "
            "features. Use as a spatial susceptibility prior, not as a full "
            "terrain/rainfall landslide predictor."
        ),
        "params": params,
        "weights": weights.tolist(),
        "bias": float(bias),
    }
    save_json(args.model_out, model)

    test_scores = 1.0 / (1.0 + np.exp(-np.clip(X_test @ weights + bias, -35.0, 35.0)))
    train_scores = 1.0 / (1.0 + np.exp(-np.clip(X_train @ weights + bias, -35.0, 35.0)))
    all_scores = predict_scores(latlon, model)
    eval_predictions = training_points.copy()
    eval_predictions["split"] = "unused"
    eval_predictions.loc[train_idx, "split"] = "train"
    eval_predictions.loc[test_idx, "split"] = "test"
    eval_predictions["landslide_susceptibility"] = all_scores
    args.eval_out.parent.mkdir(parents=True, exist_ok=True)
    eval_predictions.to_csv(args.eval_out, index=False)

    metrics = {
        "model_type": model["model_type"],
        "inventory_rows_after_coordinate_deduplication": int(len(positives)),
        "pseudo_background_rows": int(background_count),
        "training_points_path": str(args.training_out),
        "eval_predictions_path": str(args.eval_out),
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "spatial_block_degrees": float(args.block_degrees),
        "positive_train_rows": int(np.sum(y_train == 1)),
        "background_train_rows": int(np.sum(y_train == 0)),
        "positive_test_rows": int(np.sum(y_test == 1)),
        "background_test_rows": int(np.sum(y_test == 0)),
        "rbf_centers": int(len(centers)),
        "rbf_sigma_km": float(params["rbf_sigma_km"]),
        "train_roc_auc": float(roc_auc_score(y_train, train_scores)),
        "test_roc_auc": float(roc_auc_score(y_test, test_scores)),
        "train_average_precision": float(average_precision_score(y_train, train_scores)),
        "test_average_precision": float(average_precision_score(y_test, test_scores)),
        "test_threshold_metrics": binary_metrics(y_test, test_scores, threshold=0.5),
        "test_best_f1_threshold_metrics": best_f1_threshold_metrics(y_test, test_scores),
        "final_training_loss": float(losses[-1]),
        "loss_history": [float(value) for value in losses],
        "limitations": [
            "Uses latitude/longitude and RBF spatial features only.",
            "Uses sampled pseudo-background points, not surveyed non-landslide sites.",
            "Scores reflect historic spatial similarity and inventory/reporting bias.",
            "Add DEM, rainfall, lithology, land cover, roads, rivers, and fault data for a stronger model.",
        ],
    }
    save_json(args.metrics_out, metrics)

    grid_latlon = make_prediction_grid(
        positive_latlon,
        buffer_degrees=args.background_buffer_degrees,
        step_degrees=args.grid_step_degrees,
    )
    grid_scores = predict_scores(grid_latlon, model)
    write_prediction_csv(args.grid_out, grid_latlon, grid_scores)

    print(f"Wrote training points to {args.training_out}")
    print(f"Wrote model to {args.model_out}")
    print(f"Wrote metrics to {args.metrics_out}")
    print(f"Wrote train/test predictions to {args.eval_out}")
    print(f"Wrote susceptibility grid to {args.grid_out}")
    print(
        "Test ROC-AUC: "
        f"{metrics['test_roc_auc']:.3f}; "
        "Test average precision: "
        f"{metrics['test_average_precision']:.3f}"
    )


if __name__ == "__main__":
    main()
