#!/usr/bin/env python3
"""Build a landslide training table enriched with NASA, USGS, and OpenWeather APIs."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from api_feature_lib import (
    earthquake_features_for_point,
    fetch_nasa_power_daily,
    fetch_openweather_day_summary,
    fetch_usgs_earthquakes,
    nasa_features_from_response,
    openweather_features_from_response,
    openweather_key,
    parse_inventory_event_date,
    quantize_coordinate,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default=Path("data/processed/landslide_inventory.csv"), type=Path)
    parser.add_argument(
        "--background",
        default=Path("data/features/spatial_baseline_training_points.csv"),
        type=Path,
        help="CSV with label=0 pseudo-background points. Created by train_spatial_baseline.py.",
    )
    parser.add_argument("--out", default=Path("data/features/api_training_points.csv"), type=Path)
    parser.add_argument("--cache-dir", default=Path("data/cache/api"), type=Path)
    parser.add_argument("--positive-limit", default=250, type=int)
    parser.add_argument("--background-ratio", default=1.0, type=float)
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument("--nasa-lookback-days", default=90, type=int)
    parser.add_argument("--max-nasa-calls", default=500, type=int)
    parser.add_argument("--skip-nasa", action="store_true")
    parser.add_argument("--skip-usgs", action="store_true")
    parser.add_argument("--include-openweather", action="store_true")
    parser.add_argument("--max-openweather-calls", default=200, type=int)
    parser.add_argument("--usgs-lookback-days", default=3650, type=int)
    parser.add_argument("--usgs-radius-km", default=250.0, type=float)
    parser.add_argument("--usgs-min-magnitude", default=4.0, type=float)
    return parser.parse_args()


def load_positive_samples(path: Path, limit: int, seed: int) -> pd.DataFrame:
    inventory = pd.read_csv(path)
    inventory["event_date"] = inventory.apply(parse_inventory_event_date, axis=1)
    positives = inventory.dropna(subset=["latitude", "longitude", "event_date"]).copy()
    positives = positives[positives["event_date"] >= date(1981, 1, 1)]
    positives = positives[positives["event_date"] <= date.today()]
    positives = positives.drop_duplicates(["latitude", "longitude", "event_date"])
    if limit and len(positives) > limit:
        positives = positives.sample(n=limit, random_state=seed)
    positives = positives[["latitude", "longitude", "event_date"]].copy()
    positives["label"] = 1
    positives["sample_type"] = "landslide_inventory"
    return positives


def load_background_samples(
    path: Path,
    positives: pd.DataFrame,
    ratio: float,
    seed: int,
) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(
            f"Background file not found: {path}. Run scripts/train_spatial_baseline.py first."
        )
    rng = np.random.default_rng(seed)
    background = pd.read_csv(path)
    background = background[background["label"].eq(0)].dropna(subset=["latitude", "longitude"])
    count = int(round(len(positives) * ratio))
    if len(background) > count:
        background = background.sample(n=count, random_state=seed)
    dates = positives["event_date"].sample(n=len(background), replace=True, random_state=seed).to_list()
    background = background[["latitude", "longitude"]].copy()
    background["event_date"] = dates
    background["label"] = 0
    background["sample_type"] = "pseudo_background"
    return background


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    dates = pd.to_datetime(df["event_date"])
    df["event_year"] = dates.dt.year
    df["event_month"] = dates.dt.month
    df["event_dayofyear"] = dates.dt.dayofyear
    df["event_is_monsoon"] = df["event_month"].isin([6, 7, 8, 9]).astype(int)
    df["lat_round_05"] = df["latitude"].map(lambda value: quantize_coordinate(float(value), 0.5))
    df["lon_round_05"] = df["longitude"].map(lambda value: quantize_coordinate(float(value), 0.5))
    return df


def add_nasa_features(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    if args.skip_nasa:
        return df
    rows = []
    call_count = 0
    for idx, row in df.iterrows():
        if args.max_nasa_calls >= 0 and call_count >= args.max_nasa_calls:
            break
        event_date = row["event_date"]
        start_date = event_date - timedelta(days=args.nasa_lookback_days - 1)
        latitude = quantize_coordinate(float(row["latitude"]), 0.5)
        longitude = quantize_coordinate(float(row["longitude"]), 0.5)
        payload = fetch_nasa_power_daily(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=event_date,
            cache_dir=args.cache_dir,
        )
        call_count += 1
        rows.append((idx, nasa_features_from_response(payload)))
    for idx, features in rows:
        for key, value in features.items():
            df.loc[idx, key] = value
    return df


def add_usgs_features(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    if args.skip_usgs:
        return df
    min_event_date = min(df["event_date"]) - timedelta(days=args.usgs_lookback_days)
    max_event_date = max(df["event_date"]) + timedelta(days=1)
    earthquakes = fetch_usgs_earthquakes(
        min_latitude=float(df["latitude"].min()) - 3.0,
        max_latitude=float(df["latitude"].max()) + 3.0,
        min_longitude=float(df["longitude"].min()) - 3.0,
        max_longitude=float(df["longitude"].max()) + 3.0,
        start_date=min_event_date,
        end_date=max_event_date,
        min_magnitude=args.usgs_min_magnitude,
        cache_dir=args.cache_dir,
    )
    for idx, row in df.iterrows():
        features = earthquake_features_for_point(
            earthquakes=earthquakes,
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            event_date=row["event_date"],
            radius_km=args.usgs_radius_km,
            lookback_days=args.usgs_lookback_days,
        )
        for key, value in features.items():
            df.loc[idx, key] = value
    return df


def add_openweather_features(df: pd.DataFrame, args: argparse.Namespace) -> pd.DataFrame:
    if not args.include_openweather:
        return df
    api_key = openweather_key()
    if not api_key:
        print("Skipping OpenWeather: set OPENWEATHER_API_KEY to enable historical features.")
        return df
    call_count = 0
    for idx, row in df.iterrows():
        if args.max_openweather_calls >= 0 and call_count >= args.max_openweather_calls:
            break
        payload = fetch_openweather_day_summary(
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            event_date=row["event_date"],
            cache_dir=args.cache_dir,
            api_key=api_key,
        )
        call_count += 1
        for key, value in openweather_features_from_response(payload).items():
            df.loc[idx, key] = value
    return df


def main() -> None:
    args = parse_args()
    positives = load_positive_samples(args.inventory, args.positive_limit, args.seed)
    background = load_background_samples(args.background, positives, args.background_ratio, args.seed)
    df = pd.concat([positives, background], ignore_index=True)
    df = df.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    df = add_calendar_features(df)
    df = add_nasa_features(df, args)
    df = add_usgs_features(df, args)
    df = add_openweather_features(df, args)
    df["event_date"] = df["event_date"].astype(str)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df):,} API-enriched training rows to {args.out}")
    feature_cols = [col for col in df.columns if col.startswith(("nasa_", "usgs_", "ow_"))]
    print("API feature columns:", ", ".join(feature_cols) if feature_cols else "none")


if __name__ == "__main__":
    main()
