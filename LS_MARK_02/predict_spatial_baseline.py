#!/usr/bin/env python3
"""Predict landslide susceptibility scores for points with latitude/longitude."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from spatial_baseline_lib import load_json, predict_scores


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default=Path("models/spatial_baseline_model.json"),
        type=Path,
        help="Trained spatial baseline model JSON.",
    )
    parser.add_argument(
        "--points",
        required=True,
        type=Path,
        help="CSV with latitude and longitude columns.",
    )
    parser.add_argument(
        "--out",
        default=Path("reports/spatial_baseline_point_predictions.csv"),
        type=Path,
        help="Output CSV with landslide_susceptibility scores.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = load_json(args.model)
    points = pd.read_csv(args.points)
    required = {"latitude", "longitude"}
    missing = required - set(points.columns)
    if missing:
        raise SystemExit(f"Input points file is missing columns: {sorted(missing)}")

    latlon = points[["latitude", "longitude"]].to_numpy(dtype=float)
    points["landslide_susceptibility"] = predict_scores(latlon, model)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    points.to_csv(args.out, index=False)
    print(f"Wrote predictions to {args.out}")


if __name__ == "__main__":
    main()
