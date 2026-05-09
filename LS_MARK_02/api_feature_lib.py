"""API feature helpers for landslide model training."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


NASA_POWER_DAILY_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
USGS_EARTHQUAKE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
OPENWEATHER_DAILY_URL = "https://api.openweathermap.org/data/3.0/onecall/day_summary"

NASA_PARAMETERS = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS10M"]
MONTH_LOOKUP = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def stable_cache_path(cache_dir: Path, provider: str, url: str, params: dict[str, Any]) -> Path:
    safe_params = {k: v for k, v in params.items() if k.lower() not in {"appid", "api_key"}}
    payload = json.dumps({"url": url, "params": safe_params}, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return cache_dir / provider / f"{digest}.json"


def get_json_cached(
    url: str,
    params: dict[str, Any],
    cache_dir: Path,
    provider: str,
    sleep_seconds: float = 0.0,
    timeout: int = 60,
) -> dict[str, Any]:
    cache_path = stable_cache_path(cache_dir, provider, url, params)
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    request_url = f"{url}?{urlencode(params)}"
    request = Request(request_url, headers={"User-Agent": "LS-mark-01-landslide-model/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if sleep_seconds > 0:
        time.sleep(sleep_seconds)
    return payload


def parse_inventory_event_date(row: pd.Series) -> date | None:
    text = " ".join(
        str(row.get(column, ""))
        for column in ["history_date_raw", "initiation_year_raw", "event_year"]
        if pd.notna(row.get(column, None))
    )

    match = re.search(r"(\d{1,2})[./-](\d{1,2})[./-]((?:19|20)\d{2})", text)
    if match:
        day, month, year = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return safe_date(year, month, day)

    match = re.search(r"((?:19|20)\d{2})-(\d{1,2})-(\d{1,2})", text)
    if match:
        year, month, day = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return safe_date(year, month, day)

    lower_text = text.lower()
    year_match = re.search(r"(?:19|20)\d{2}", lower_text)
    if not year_match:
        return None

    year = int(year_match.group(0))
    for month_name, month in MONTH_LOOKUP.items():
        if re.search(rf"\b{re.escape(month_name)}\b", lower_text):
            return safe_date(year, month, 15)

    return safe_date(year, 7, 15)


def safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def date_to_yyyymmdd(value: date) -> str:
    return value.strftime("%Y%m%d")


def quantize_coordinate(value: float, step: float = 0.5) -> float:
    return round(round(value / step) * step, 4)


def haversine_km(lat1: np.ndarray, lon1: np.ndarray, lat2: float, lon2: float) -> np.ndarray:
    radius = 6371.0088
    lat1_rad = np.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = lat1_rad - lat2_rad
    delta_lon = np.radians(lon1 - lon2)
    a = (
        np.sin(delta_lat / 2.0) ** 2
        + np.cos(lat1_rad) * math.cos(lat2_rad) * np.sin(delta_lon / 2.0) ** 2
    )
    return radius * 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))


def fetch_nasa_power_daily(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
    cache_dir: Path,
) -> dict[str, Any]:
    params = {
        "parameters": ",".join(NASA_PARAMETERS),
        "community": "AG",
        "longitude": f"{longitude:.4f}",
        "latitude": f"{latitude:.4f}",
        "start": date_to_yyyymmdd(start_date),
        "end": date_to_yyyymmdd(end_date),
        "format": "JSON",
        "time-standard": "UTC",
    }
    return get_json_cached(NASA_POWER_DAILY_URL, params, cache_dir, "nasa_power", sleep_seconds=0.15)


def nasa_features_from_response(payload: dict[str, Any]) -> dict[str, float]:
    parameters = payload.get("properties", {}).get("parameter", {})
    features: dict[str, float] = {}

    precipitation = pd.Series(parameters.get("PRECTOTCORR", {}), dtype="float64")
    t2m = pd.Series(parameters.get("T2M", {}), dtype="float64")
    t2m_max = pd.Series(parameters.get("T2M_MAX", {}), dtype="float64")
    t2m_min = pd.Series(parameters.get("T2M_MIN", {}), dtype="float64")
    rh2m = pd.Series(parameters.get("RH2M", {}), dtype="float64")
    ws10m = pd.Series(parameters.get("WS10M", {}), dtype="float64")

    if not precipitation.empty:
        features["nasa_precip_7d_mm"] = float(precipitation.tail(7).sum())
        features["nasa_precip_30d_mm"] = float(precipitation.tail(30).sum())
        features["nasa_precip_90d_mm"] = float(precipitation.tail(90).sum())
        features["nasa_precip_max_1d_mm"] = float(precipitation.max())
        features["nasa_rainy_days_30d"] = float((precipitation.tail(30) > 1.0).sum())
    if not t2m.empty:
        features["nasa_t2m_30d_mean_c"] = float(t2m.tail(30).mean())
    if not t2m_max.empty:
        features["nasa_t2m_max_30d_mean_c"] = float(t2m_max.tail(30).mean())
    if not t2m_min.empty:
        features["nasa_t2m_min_30d_mean_c"] = float(t2m_min.tail(30).mean())
    if not rh2m.empty:
        features["nasa_rh2m_30d_mean_pct"] = float(rh2m.tail(30).mean())
    if not ws10m.empty:
        features["nasa_ws10m_30d_mean_ms"] = float(ws10m.tail(30).mean())

    return features


def fetch_usgs_earthquakes(
    min_latitude: float,
    max_latitude: float,
    min_longitude: float,
    max_longitude: float,
    start_date: date,
    end_date: date,
    min_magnitude: float,
    cache_dir: Path,
) -> pd.DataFrame:
    params = {
        "format": "geojson",
        "starttime": start_date.isoformat(),
        "endtime": end_date.isoformat(),
        "minlatitude": f"{min_latitude:.4f}",
        "maxlatitude": f"{max_latitude:.4f}",
        "minlongitude": f"{min_longitude:.4f}",
        "maxlongitude": f"{max_longitude:.4f}",
        "minmagnitude": f"{min_magnitude:.1f}",
        "eventtype": "earthquake",
        "limit": 20000,
    }
    payload = get_json_cached(USGS_EARTHQUAKE_URL, params, cache_dir, "usgs_earthquake")
    rows = []
    for feature in payload.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates") or [np.nan, np.nan, np.nan]
        event_time = properties.get("time")
        rows.append(
            {
                "event_time": pd.to_datetime(event_time, unit="ms", utc=True, errors="coerce"),
                "longitude": coordinates[0],
                "latitude": coordinates[1],
                "depth_km": coordinates[2] if len(coordinates) > 2 else np.nan,
                "magnitude": properties.get("mag"),
            }
        )
    return pd.DataFrame(rows)


def earthquake_features_for_point(
    earthquakes: pd.DataFrame,
    latitude: float,
    longitude: float,
    event_date: date,
    radius_km: float,
    lookback_days: int,
) -> dict[str, float]:
    columns = {
        "usgs_eq_count": 0.0,
        "usgs_eq_max_mag": 0.0,
        "usgs_eq_nearest_km": 9999.0,
        "usgs_eq_mag_distance_score": 0.0,
        "usgs_eq_days_since_nearest": 9999.0,
    }
    if earthquakes.empty:
        return columns

    end = pd.Timestamp(datetime.combine(event_date, datetime.min.time(), tzinfo=timezone.utc))
    start = end - pd.Timedelta(days=lookback_days)
    window = earthquakes[
        (earthquakes["event_time"] >= start)
        & (earthquakes["event_time"] <= end)
        & earthquakes["latitude"].notna()
        & earthquakes["longitude"].notna()
    ].copy()
    if window.empty:
        return columns

    distances = haversine_km(
        window["latitude"].to_numpy(dtype=float),
        window["longitude"].to_numpy(dtype=float),
        latitude,
        longitude,
    )
    window = window.assign(distance_km=distances)
    window = window[window["distance_km"] <= radius_km]
    if window.empty:
        return columns

    nearest_idx = window["distance_km"].idxmin()
    nearest_time = window.loc[nearest_idx, "event_time"]
    days_since = (end - nearest_time).total_seconds() / 86400.0
    magnitude = window["magnitude"].fillna(0.0).to_numpy(dtype=float)
    distance = window["distance_km"].to_numpy(dtype=float)
    columns.update(
        {
            "usgs_eq_count": float(len(window)),
            "usgs_eq_max_mag": float(window["magnitude"].max()),
            "usgs_eq_nearest_km": float(window["distance_km"].min()),
            "usgs_eq_mag_distance_score": float(np.sum(magnitude / (1.0 + distance))),
            "usgs_eq_days_since_nearest": float(days_since),
        }
    )
    return columns


def openweather_key() -> str | None:
    return os.environ.get("OPENWEATHER_API_KEY") or os.environ.get("OWM_API_KEY")


def fetch_openweather_day_summary(
    latitude: float,
    longitude: float,
    event_date: date,
    cache_dir: Path,
    api_key: str,
) -> dict[str, Any]:
    params = {
        "lat": f"{latitude:.6f}",
        "lon": f"{longitude:.6f}",
        "date": event_date.isoformat(),
        "units": "metric",
        "appid": api_key,
    }
    return get_json_cached(OPENWEATHER_DAILY_URL, params, cache_dir, "openweather", sleep_seconds=0.15)


def openweather_features_from_response(payload: dict[str, Any]) -> dict[str, float]:
    def nested(*keys: str) -> float:
        current: Any = payload
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return np.nan
            current = current[key]
        try:
            return float(current)
        except (TypeError, ValueError):
            return np.nan

    return {
        "ow_temp_min_c": nested("temperature", "min"),
        "ow_temp_max_c": nested("temperature", "max"),
        "ow_temp_afternoon_c": nested("temperature", "afternoon"),
        "ow_precip_total_mm": nested("precipitation", "total"),
        "ow_humidity_afternoon_pct": nested("humidity", "afternoon"),
        "ow_pressure_afternoon_hpa": nested("pressure", "afternoon"),
        "ow_cloud_cover_afternoon_pct": nested("cloud_cover", "afternoon"),
        "ow_wind_max_ms": nested("wind", "max", "speed"),
    }
