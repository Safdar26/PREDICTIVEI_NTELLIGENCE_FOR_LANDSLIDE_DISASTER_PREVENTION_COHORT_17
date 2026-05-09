#!/usr/bin/env python3
"""Train a landslide model from API-enriched features."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from spatial_baseline_lib import (
    average_precision_score,
    best_f1_threshold_metrics,
    binary_metrics,
    roc_auc_score,
    spatial_train_test_split,
    train_logistic_regression,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", default=Path("data/features/api_training_points.csv"), type=Path)
    parser.add_argument("--model-out", default=Path("models/external_api_landslide_model.json"), type=Path)
    parser.add_argument("--metrics-out", default=Path("reports/external_api_model_metrics.json"), type=Path)
    parser.add_argument("--eval-out", default=Path("reports/external_api_eval_predictions.csv"), type=Path)
    parser.add_argument("--epochs", default=120, type=int)
    parser.add_argument("--batch-size", default=2048, type=int)
    parser.add_argument("--learning-rate", default=0.01, type=float)
    parser.add_argument("--l2", default=0.001, type=float)
    parser.add_argument("--seed", default=42, type=int)
    return parser.parse_args()


def prepare_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str], dict[str, Any]]:
    candidate_prefixes = ("nasa_", "usgs_", "ow_")
    base_columns = ["latitude", "longitude", "event_month", "event_dayofyear", "event_is_monsoon"]
    feature_columns = [
        col
        for col in df.columns
        if col in base_columns or col.startswith(candidate_prefixes)
    ]
    numeric = df[feature_columns].apply(pd.to_numeric, errors="coerce")
    numeric = numeric.dropna(axis=1, how="all")
    feature_columns = numeric.columns.tolist()
    if not any(col.startswith(candidate_prefixes) for col in feature_columns):
        raise SystemExit("No API feature columns are populated; build API features first.")

    impute_values = numeric.median().fillna(0.0)
    numeric = numeric.fillna(impute_values)
    mean = numeric.mean()
    std = numeric.std(ddof=0).replace(0.0, 1.0)
    X = ((numeric - mean) / std).to_numpy(dtype=float)
    preprocessing = {
        "feature_columns": feature_columns,
        "impute_values": impute_values.to_dict(),
        "feature_mean": mean.to_dict(),
        "feature_std": std.to_dict(),
    }
    return X, feature_columns, preprocessing


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    df = pd.read_csv(args.features)
    required = {"label", "latitude", "longitude"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Feature table is missing required columns: {sorted(missing)}")

    X, feature_columns, preprocessing = prepare_matrix(df)
    y = df["label"].astype(int).to_numpy()
    latlon = df[["latitude", "longitude"]].to_numpy(dtype=float)
    train_idx, test_idx = spatial_train_test_split(
        latlon,
        y.astype(float),
        rng=rng,
        block_degrees=1.0,
        test_fraction=0.25,
    )

    weights, bias, losses = train_logistic_regression(
        X[train_idx],
        y[train_idx].astype(float),
        rng=rng,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        l2=args.l2,
    )
    train_scores = 1.0 / (1.0 + np.exp(-np.clip(X[train_idx] @ weights + bias, -35.0, 35.0)))
    test_scores = 1.0 / (1.0 + np.exp(-np.clip(X[test_idx] @ weights + bias, -35.0, 35.0)))
    all_scores = 1.0 / (1.0 + np.exp(-np.clip(X @ weights + bias, -35.0, 35.0)))

    model = {
        "model_type": "external_api_logistic_landslide_model",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "feature_sources": ["NASA POWER", "USGS Earthquake", "OpenWeather if enabled"],
        "preprocessing": preprocessing,
        "weights": weights.tolist(),
        "bias": float(bias),
    }
    metrics = {
        "model_type": model["model_type"],
        "rows": int(len(df)),
        "features_path": str(args.features),
        "eval_predictions_path": str(args.eval_out),
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "feature_columns": feature_columns,
        "train_roc_auc": float(roc_auc_score(y[train_idx], train_scores)),
        "test_roc_auc": float(roc_auc_score(y[test_idx], test_scores)),
        "train_average_precision": float(average_precision_score(y[train_idx], train_scores)),
        "test_average_precision": float(average_precision_score(y[test_idx], test_scores)),
        "test_threshold_metrics": binary_metrics(y[test_idx], test_scores, threshold=0.5),
        "test_best_f1_threshold_metrics": best_f1_threshold_metrics(y[test_idx], test_scores),
        "final_training_loss": float(losses[-1]),
        "loss_history": [float(value) for value in losses],
    }
    eval_predictions = df.copy()
    eval_predictions["split"] = "unused"
    eval_predictions.loc[train_idx, "split"] = "train"
    eval_predictions.loc[test_idx, "split"] = "test"
    eval_predictions["landslide_susceptibility"] = all_scores
    args.eval_out.parent.mkdir(parents=True, exist_ok=True)
    eval_predictions.to_csv(args.eval_out, index=False)

    save_json(args.model_out, model)
    save_json(args.metrics_out, metrics)
    print(f"Wrote model to {args.model_out}")
    print(f"Wrote metrics to {args.metrics_out}")
    print(f"Wrote train/test predictions to {args.eval_out}")
    print(f"Test ROC-AUC: {metrics['test_roc_auc']:.3f}")


if __name__ == "__main__":
    main()
