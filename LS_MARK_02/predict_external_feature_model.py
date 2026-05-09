#!/usr/bin/env python3
"""Predict landslide susceptibility from an API-enriched feature CSV."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=Path("models/external_api_landslide_model.json"), type=Path)
    parser.add_argument("--features", default=Path("data/features/api_training_points.csv"), type=Path)
    parser.add_argument("--out", default=Path("reports/external_api_predictions.csv"), type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = json.loads(args.model.read_text(encoding="utf-8"))
    df = pd.read_csv(args.features)
    preprocessing = model["preprocessing"]
    columns = preprocessing["feature_columns"]
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise SystemExit(f"Feature table is missing model columns: {missing}")

    numeric = df[columns].apply(pd.to_numeric, errors="coerce")
    impute = pd.Series(preprocessing["impute_values"])
    mean = pd.Series(preprocessing["feature_mean"])
    std = pd.Series(preprocessing["feature_std"]).replace(0.0, 1.0)
    X = ((numeric.fillna(impute) - mean) / std).to_numpy(dtype=float)
    weights = np.array(model["weights"], dtype=float)
    bias = float(model["bias"])
    scores = 1.0 / (1.0 + np.exp(-np.clip(X @ weights + bias, -35.0, 35.0)))

    output = df.copy()
    output["landslide_susceptibility"] = scores
    args.out.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.out, index=False)
    print(f"Wrote predictions to {args.out}")


if __name__ == "__main__":
    main()
