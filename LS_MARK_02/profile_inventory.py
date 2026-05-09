#!/usr/bin/env python3
"""Create a compact markdown profile of the extracted landslide inventory."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv",
        default=Path("data/processed/landslide_inventory.csv"),
        type=Path,
        help="Extracted inventory CSV.",
    )
    parser.add_argument(
        "--out",
        default=Path("reports/inventory_profile.md"),
        type=Path,
        help="Markdown report path.",
    )
    return parser.parse_args()


def markdown_table(series: pd.Series, value_name: str, limit: int = 15) -> str:
    rows = [f"| {series.name or 'value'} | {value_name} |", "|---|---:|"]
    for index, value in series.head(limit).items():
        rows.append(f"| {index} | {int(value):,} |")
    return "\n".join(rows)


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.csv)

    known_years = df["event_year"].dropna()
    year_range = (
        f"{int(known_years.min())} to {int(known_years.max())}"
        if not known_years.empty
        else "not available"
    )

    duplicate_coordinates = df.duplicated(["latitude", "longitude"]).sum()
    state_column = "state_normalized" if "state_normalized" in df.columns else "state"

    duplicate_events = df.duplicated(
        [
            "latitude",
            "longitude",
            state_column,
            "district",
            "material_involved",
            "movement_type",
            "event_year",
        ]
    ).sum()

    lines = [
        "# Landslide Inventory Profile",
        "",
        "## Overview",
        "",
        f"- Records: {len(df):,}",
        f"- S.No range: {int(df['s_no'].min()):,} to {int(df['s_no'].max()):,}",
        f"- Normalized states/UT labels: {df[state_column].nunique():,}",
        f"- Raw state labels: {df['state'].nunique():,}",
        f"- Known event years: {int(df['event_year'].notna().sum()):,}",
        f"- Unknown event years: {int(df['event_year'].isna().sum()):,}",
        f"- Event year range: {year_range}",
        f"- Duplicate coordinate rows: {int(duplicate_coordinates):,}",
        f"- Duplicate event-like rows: {int(duplicate_events):,}",
        "",
        "## Top States/UT Labels",
        "",
        markdown_table(df[state_column].fillna("").value_counts(), "records"),
        "",
        "## Material Involved",
        "",
        markdown_table(df["material_involved"].fillna("").value_counts(), "records"),
        "",
        "## Movement Type",
        "",
        markdown_table(df["movement_type"].fillna("").value_counts(), "records"),
        "",
        "## Top Event Years",
        "",
        markdown_table(
            df["event_year"].dropna().astype(int).value_counts().sort_index(),
            "records",
            limit=30,
        ),
        "",
        "## Modeling Notes",
        "",
        "This CSV is a landslide occurrence inventory. It is suitable as positive",
        "samples, but by itself it is not enough to train a defensible prediction",
        "model. Add background or non-landslide samples and spatial covariates such",
        "as slope, aspect, rainfall, lithology, land cover, drainage distance, road",
        "distance, and fault distance before fitting a classifier.",
        "",
    ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote profile to {args.out}")


if __name__ == "__main__":
    main()
