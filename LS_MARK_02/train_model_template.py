#!/usr/bin/env python3
"""Train a baseline landslide susceptibility classifier from a feature table.

Input must be a CSV with one row per point or grid cell. It should contain:

- label: 1 for landslide, 0 for non-landslide/background
- latitude, longitude: WGS84 point coordinates
- numeric predictor columns, for example slope, rainfall, lithology_code

This script intentionally does not train from the PDF inventory alone because
that inventory only contains positive landslide occurrences.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--features",
        default=Path("data/features/training_points.csv"),
        type=Path,
        help="CSV with labels and predictor columns.",
    )
    parser.add_argument(
        "--model-out",
        default=Path("models/random_forest_landslide.joblib"),
        type=Path,
        help="Output model path.",
    )
    parser.add_argument(
        "--metrics-out",
        default=Path("reports/model_metrics.json"),
        type=Path,
        help="Output metrics JSON path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.features.exists():
        raise SystemExit(
            f"Feature table not found: {args.features}. Create it after extracting "
            "terrain, rainfall, geology, land-cover, and background samples."
        )

    try:
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import (
            average_precision_score,
            classification_report,
            roc_auc_score,
        )
        from sklearn.model_selection import GroupShuffleSplit, train_test_split
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing modeling dependency. Install the modeling requirements first, "
            "for example: python -m pip install -r requirements-modeling.txt"
        ) from exc

    df = pd.read_csv(args.features)

    required = {"label", "latitude", "longitude"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Feature table is missing required columns: {sorted(missing)}")

    numeric = df.select_dtypes(include=["number"]).columns.tolist()
    ignored = {"label", "latitude", "longitude", "s_no", "event_year"}
    feature_columns = [column for column in numeric if column not in ignored]
    if not feature_columns:
        raise SystemExit("No numeric predictor columns found.")

    X = df[feature_columns]
    y = df["label"].astype(int)

    if "spatial_block_id" in df.columns:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
        train_idx, test_idx = next(splitter.split(X, y, groups=df["spatial_block_id"]))
    else:
        train_idx, test_idx = train_test_split(
            df.index,
            test_size=0.25,
            random_state=42,
            stratify=y,
        )

    model = RandomForestClassifier(
        n_estimators=400,
        min_samples_leaf=3,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X.loc[train_idx], y.loc[train_idx])

    probabilities = model.predict_proba(X.loc[test_idx])[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    metrics = {
        "rows": int(len(df)),
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "feature_columns": feature_columns,
        "roc_auc": float(roc_auc_score(y.loc[test_idx], probabilities)),
        "average_precision": float(
            average_precision_score(y.loc[test_idx], probabilities)
        ),
        "classification_report": classification_report(
            y.loc[test_idx],
            predictions,
            output_dict=True,
            zero_division=0,
        ),
    }

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_columns": feature_columns}, args.model_out)
    args.metrics_out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Wrote model to {args.model_out}")
    print(f"Wrote metrics to {args.metrics_out}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
