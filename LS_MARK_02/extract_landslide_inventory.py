#!/usr/bin/env python3
"""Extract the field-validated landslide inventory PDF into a CSV table.

The source PDF is an Excel export with fixed-width columns. Using pypdf's
layout extraction keeps those columns aligned, which is more reliable than
parsing the default free-text extraction.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
from pypdf import PdfReader


RAW_HEADERS = [
    "S.No",
    "Latitude",
    "Longitude",
    "Slide_Name",
    "State",
    "District",
    "Subdivision Or Taluk",
    "Material Involved",
    "Movement Type",
    "Initiation_Year",
    "History_date",
]

HEADER_TO_LEFT_EDGE_OFFSETS = [
    0,
    -3,
    -5,
    -16,
    -13,
    -10,
    -4,
    -4,
    -1,
    -2,
    -5,
]

RAW_VALUE_COLUMNS = [
    "s_no",
    "latitude",
    "longitude",
    "slide_name",
    "state",
    "district",
    "subdivision_or_taluk",
    "material_involved",
    "movement_type",
    "initiation_year_raw",
    "history_date_raw",
]

OUTPUT_COLUMNS = [
    "s_no",
    "latitude",
    "longitude",
    "slide_name",
    "state",
    "state_normalized",
    "district",
    "subdivision_or_taluk",
    "material_involved",
    "movement_type",
    "initiation_year_raw",
    "history_date_raw",
    "event_year",
    "source_page",
]

YEAR_PATTERN = re.compile(r"(?:18|19|20)\d{2}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pdf",
        default="landslide_report.pdf",
        type=Path,
        help="Path to the landslide inventory PDF.",
    )
    parser.add_argument(
        "--out",
        default=Path("data/processed/landslide_inventory.csv"),
        type=Path,
        help="CSV path to write.",
    )
    parser.add_argument(
        "--summary",
        default=Path("data/processed/landslide_inventory_summary.json"),
        type=Path,
        help="JSON extraction summary path to write.",
    )
    return parser.parse_args()


def header_positions(header_line: str) -> list[int]:
    positions: list[int] = []
    for header, offset in zip(RAW_HEADERS, HEADER_TO_LEFT_EDGE_OFFSETS):
        pos = header_line.find(header)
        if pos < 0:
            raise ValueError(f"Could not find header {header!r} in {header_line!r}")
        positions.append(max(0, pos + offset))
    if positions != sorted(positions):
        raise ValueError(f"Detected non-increasing column positions: {positions}")
    return positions


def split_fixed_columns(line: str, starts: list[int]) -> list[str]:
    values: list[str] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else None
        values.append(line[start:end].strip())
    return values


def is_number(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def is_row_start(values: list[str]) -> bool:
    return (
        len(values) >= 3
        and values[0].isdigit()
        and is_number(values[1])
        and is_number(values[2])
    )


def join_parts(parts: Iterable[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def merge_pending(pending: list[str], values: list[str]) -> list[str]:
    return [join_parts([before, current]) for before, current in zip(pending, values)]


def normalise_title(value: str) -> str:
    value = value.strip()
    if not value:
        return value
    return " ".join(token.capitalize() for token in value.split())


def normalise_state(value: str) -> str:
    value = " ".join(value.split())
    if not value:
        return value

    key = value.lower().replace("&", "and")
    aliases = {
        "jammu and kashmir": "Jammu & Kashmir",
        "ut: jammu and kashmir": "Jammu & Kashmir",
        "ut: ladakh": "Ladakh",
        "karnataka": "Karnataka",
        "nagaland": "Nagaland",
    }
    if key in aliases:
        return aliases[key]
    if value.isupper():
        return value.title()
    return value


def extract_event_year(initiation_year: str, history_date: str) -> int | None:
    initiation_year = initiation_year.strip()
    history_date = history_date.strip()

    if initiation_year and initiation_year not in {"0", "Nil", "NIL", "nil"}:
        match = YEAR_PATTERN.search(initiation_year)
        if match:
            return int(match.group(0))
        if initiation_year.isdigit() and len(initiation_year) == 4:
            return int(initiation_year)

    if history_date and history_date not in {"0", "Nil", "NIL", "nil"}:
        match = YEAR_PATTERN.search(history_date)
        if match:
            return int(match.group(0))

    return None


def page_rows(page_text: str, source_page: int) -> tuple[list[dict[str, object]], int]:
    lines = page_text.splitlines()
    header_line = next(
        (
            line
            for line in lines
            if "S.No" in line and "Latitude" in line and "History_date" in line
        ),
        None,
    )
    if header_line is None:
        return [], 0

    starts = header_positions(header_line)
    rows: list[dict[str, object]] = []
    pending = [""] * len(RAW_HEADERS)
    reached_header = False
    dropped_pending_lines = 0

    for line in lines:
        if line == header_line:
            reached_header = True
            continue
        if not reached_header:
            continue
        if not line.strip():
            continue
        if re.fullmatch(r"\s*Page\s+\d+\s*", line):
            continue

        values = split_fixed_columns(line, starts)

        if is_row_start(values):
            values = merge_pending(pending, values)
            pending = [""] * len(RAW_HEADERS)

            record = dict(zip(RAW_VALUE_COLUMNS, values))
            record["s_no"] = int(record["s_no"])
            record["latitude"] = float(record["latitude"])
            record["longitude"] = float(record["longitude"])
            record["state_normalized"] = normalise_state(str(record["state"]))
            record["material_involved"] = normalise_title(str(record["material_involved"]))
            record["movement_type"] = normalise_title(str(record["movement_type"]))
            record["event_year"] = extract_event_year(
                str(record["initiation_year_raw"]),
                str(record["history_date_raw"]),
            )
            record["source_page"] = source_page
            rows.append(record)
            continue

        if any(value.strip() for value in values):
            pending = merge_pending(pending, values)

    if any(value.strip() for value in pending):
        dropped_pending_lines += 1

    return rows, dropped_pending_lines


def extract_inventory(pdf_path: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    reader = PdfReader(str(pdf_path))
    all_rows: list[dict[str, object]] = []
    pages_with_dropped_pending = 0

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text(extraction_mode="layout") or ""
        rows, dropped_pending = page_rows(text, page_number)
        all_rows.extend(rows)
        pages_with_dropped_pending += dropped_pending

    df = pd.DataFrame(all_rows, columns=OUTPUT_COLUMNS)
    if df.empty:
        raise RuntimeError(f"No rows extracted from {pdf_path}")

    df = df.sort_values("s_no").reset_index(drop=True)
    expected = set(range(int(df["s_no"].min()), int(df["s_no"].max()) + 1))
    observed = set(int(value) for value in df["s_no"])
    missing = sorted(expected - observed)

    summary = {
        "source_pdf": str(pdf_path),
        "rows": int(len(df)),
        "min_s_no": int(df["s_no"].min()),
        "max_s_no": int(df["s_no"].max()),
        "missing_s_no_count": int(len(missing)),
        "missing_s_no_sample": missing[:25],
        "duplicate_s_no_count": int(df["s_no"].duplicated().sum()),
        "known_event_year_count": int(df["event_year"].notna().sum()),
        "unknown_event_year_count": int(df["event_year"].isna().sum()),
        "raw_state_label_count": int(df["state"].nunique(dropna=True)),
        "normalized_state_label_count": int(df["state_normalized"].nunique(dropna=True)),
        "pages_with_dropped_pending": int(pages_with_dropped_pending),
    }
    return df, summary


def main() -> None:
    args = parse_args()
    df, summary = extract_inventory(args.pdf)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote {len(df):,} rows to {args.out}")
    print(f"Wrote summary to {args.summary}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
