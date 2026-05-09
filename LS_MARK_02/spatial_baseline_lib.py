"""Utilities for the landslide spatial susceptibility baseline."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


EARTH_KM_PER_DEGREE_LAT = 110.574
EARTH_KM_PER_DEGREE_LON_AT_EQUATOR = 111.320


def sigmoid(values: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -35.0, 35.0)))


def latlon_to_xy(
    latitude: np.ndarray,
    longitude: np.ndarray,
    origin_latitude: float,
    origin_longitude: float,
    reference_latitude: float,
) -> np.ndarray:
    """Convert WGS84 lat/lon to approximate local x/y kilometers."""

    x = (
        (longitude - origin_longitude)
        * EARTH_KM_PER_DEGREE_LON_AT_EQUATOR
        * math.cos(math.radians(reference_latitude))
    )
    y = (latitude - origin_latitude) * EARTH_KM_PER_DEGREE_LAT
    return np.column_stack([x, y])


def xy_to_latlon(
    xy: np.ndarray,
    origin_latitude: float,
    origin_longitude: float,
    reference_latitude: float,
) -> np.ndarray:
    longitude = (
        xy[:, 0]
        / (EARTH_KM_PER_DEGREE_LON_AT_EQUATOR * math.cos(math.radians(reference_latitude)))
    ) + origin_longitude
    latitude = (xy[:, 1] / EARTH_KM_PER_DEGREE_LAT) + origin_latitude
    return np.column_stack([latitude, longitude])


def build_spatial_hash(xy: np.ndarray, cell_size_km: float) -> dict[tuple[int, int], list[int]]:
    cells: dict[tuple[int, int], list[int]] = {}
    cell_ids = np.floor(xy / cell_size_km).astype(int)
    for idx, cell in enumerate(cell_ids):
        key = (int(cell[0]), int(cell[1]))
        cells.setdefault(key, []).append(idx)
    return cells


def is_near_existing_point(
    point_xy: np.ndarray,
    positive_xy: np.ndarray,
    spatial_hash: dict[tuple[int, int], list[int]],
    cell_size_km: float,
    min_distance_km: float,
) -> bool:
    cell = np.floor(point_xy / cell_size_km).astype(int)
    radius_cells = int(math.ceil(min_distance_km / cell_size_km))
    min_distance_sq = min_distance_km * min_distance_km

    for dx in range(-radius_cells, radius_cells + 1):
        for dy in range(-radius_cells, radius_cells + 1):
            neighbor_key = (int(cell[0] + dx), int(cell[1] + dy))
            neighbor_indices = spatial_hash.get(neighbor_key)
            if not neighbor_indices:
                continue
            diff = positive_xy[neighbor_indices] - point_xy
            if np.any(np.sum(diff * diff, axis=1) <= min_distance_sq):
                return True
    return False


def sample_background_points(
    positive_latlon: np.ndarray,
    count: int,
    rng: np.random.Generator,
    buffer_degrees: float,
    min_distance_km: float,
) -> np.ndarray:
    """Sample pseudo-background points away from known landslide coordinates."""

    min_lat = float(np.min(positive_latlon[:, 0]) - buffer_degrees)
    max_lat = float(np.max(positive_latlon[:, 0]) + buffer_degrees)
    min_lon = float(np.min(positive_latlon[:, 1]) - buffer_degrees)
    max_lon = float(np.max(positive_latlon[:, 1]) + buffer_degrees)

    origin_latitude = min_lat
    origin_longitude = min_lon
    reference_latitude = float(np.mean(positive_latlon[:, 0]))
    positive_xy = latlon_to_xy(
        positive_latlon[:, 0],
        positive_latlon[:, 1],
        origin_latitude,
        origin_longitude,
        reference_latitude,
    )
    cell_size_km = max(1.0, min_distance_km)
    spatial_hash = build_spatial_hash(positive_xy, cell_size_km)

    accepted: list[list[float]] = []
    attempts = 0
    max_attempts = count * 200
    while len(accepted) < count and attempts < max_attempts:
        attempts += 1
        candidate_lat = float(rng.uniform(min_lat, max_lat))
        candidate_lon = float(rng.uniform(min_lon, max_lon))
        candidate_xy = latlon_to_xy(
            np.array([candidate_lat]),
            np.array([candidate_lon]),
            origin_latitude,
            origin_longitude,
            reference_latitude,
        )[0]
        if is_near_existing_point(
            candidate_xy,
            positive_xy,
            spatial_hash,
            cell_size_km,
            min_distance_km,
        ):
            continue
        accepted.append([candidate_lat, candidate_lon])

    if len(accepted) < count:
        raise RuntimeError(
            f"Only sampled {len(accepted):,} background points out of {count:,}. "
            "Try reducing --background-min-distance-km."
        )

    return np.array(accepted, dtype=float)


def spatial_block_ids(latlon: np.ndarray, block_degrees: float) -> np.ndarray:
    lat_block = np.floor(latlon[:, 0] / block_degrees).astype(int)
    lon_block = np.floor(latlon[:, 1] / block_degrees).astype(int)
    return np.array([f"{lat}_{lon}" for lat, lon in zip(lat_block, lon_block)])


def spatial_train_test_split(
    latlon: np.ndarray,
    labels: np.ndarray,
    rng: np.random.Generator,
    block_degrees: float,
    test_fraction: float,
) -> tuple[np.ndarray, np.ndarray]:
    blocks = spatial_block_ids(latlon, block_degrees)
    unique_blocks = np.unique(blocks)

    for _ in range(100):
        shuffled = rng.permutation(unique_blocks)
        test_count = max(1, int(round(len(unique_blocks) * test_fraction)))
        test_blocks = set(shuffled[:test_count])
        test_mask = np.array([block in test_blocks for block in blocks])
        train_mask = ~test_mask
        if (
            labels[test_mask].sum() > 0
            and (test_mask.sum() - labels[test_mask].sum()) > 0
            and labels[train_mask].sum() > 0
            and (train_mask.sum() - labels[train_mask].sum()) > 0
        ):
            return np.where(train_mask)[0], np.where(test_mask)[0]

    raise RuntimeError("Could not create a spatial split with both classes in each split.")


def kmeans_centers(
    xy: np.ndarray,
    center_count: int,
    rng: np.random.Generator,
    iterations: int,
) -> np.ndarray:
    if len(xy) < center_count:
        return xy.copy()

    centers = xy[rng.choice(len(xy), size=center_count, replace=False)].copy()
    for _ in range(iterations):
        distances = squared_distance_matrix(xy, centers)
        assignments = np.argmin(distances, axis=1)
        new_centers = centers.copy()
        for center_idx in range(center_count):
            member_mask = assignments == center_idx
            if np.any(member_mask):
                new_centers[center_idx] = xy[member_mask].mean(axis=0)
        if np.max(np.abs(new_centers - centers)) < 1e-4:
            centers = new_centers
            break
        centers = new_centers
    return centers


def squared_distance_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_sq = np.sum(a * a, axis=1, keepdims=True)
    b_sq = np.sum(b * b, axis=1, keepdims=True).T
    return np.maximum(a_sq + b_sq - 2.0 * (a @ b.T), 0.0)


def choose_rbf_sigma(centers: np.ndarray) -> float:
    if len(centers) < 2:
        return 100.0
    distances = np.sqrt(squared_distance_matrix(centers, centers))
    distances[distances == 0] = np.nan
    nearest = np.nanmin(distances, axis=1)
    sigma = float(np.nanmedian(nearest) * 1.5)
    return max(40.0, sigma)


def make_features(
    latlon: np.ndarray,
    model_params: dict[str, Any],
    fit_scaler: bool,
) -> tuple[np.ndarray, dict[str, Any]]:
    origin_lat = float(model_params["origin_latitude"])
    origin_lon = float(model_params["origin_longitude"])
    reference_lat = float(model_params["reference_latitude"])
    centers = np.array(model_params["centers_xy"], dtype=float)
    sigma = float(model_params["rbf_sigma_km"])

    xy = latlon_to_xy(latlon[:, 0], latlon[:, 1], origin_lat, origin_lon, reference_lat)
    raw_features = [
        xy[:, 0],
        xy[:, 1],
        xy[:, 0] * xy[:, 0],
        xy[:, 1] * xy[:, 1],
        xy[:, 0] * xy[:, 1],
    ]

    distances_sq = squared_distance_matrix(xy, centers)
    rbf_features = np.exp(-distances_sq / (2.0 * sigma * sigma))
    X = np.column_stack(raw_features + [rbf_features])

    if fit_scaler:
        mean = X.mean(axis=0)
        std = X.std(axis=0)
        std[std < 1e-8] = 1.0
        model_params["feature_mean"] = mean.tolist()
        model_params["feature_std"] = std.tolist()
    else:
        mean = np.array(model_params["feature_mean"], dtype=float)
        std = np.array(model_params["feature_std"], dtype=float)

    return (X - mean) / std, model_params


def train_logistic_regression(
    X: np.ndarray,
    y: np.ndarray,
    rng: np.random.Generator,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    l2: float,
) -> tuple[np.ndarray, float, list[float]]:
    weights = np.zeros(X.shape[1], dtype=float)
    bias = 0.0
    first_moment = np.zeros_like(weights)
    second_moment = np.zeros_like(weights)
    bias_first = 0.0
    bias_second = 0.0
    beta1 = 0.9
    beta2 = 0.999
    eps = 1e-8
    losses: list[float] = []
    step = 0

    for _ in range(epochs):
        epoch_indices = rng.permutation(len(y))
        for start in range(0, len(y), batch_size):
            step += 1
            batch_indices = epoch_indices[start : start + batch_size]
            X_batch = X[batch_indices]
            y_batch = y[batch_indices]

            probabilities = sigmoid(X_batch @ weights + bias)
            errors = probabilities - y_batch
            grad_weights = (X_batch.T @ errors) / len(y_batch) + l2 * weights
            grad_bias = float(np.mean(errors))

            first_moment = beta1 * first_moment + (1.0 - beta1) * grad_weights
            second_moment = beta2 * second_moment + (1.0 - beta2) * (grad_weights**2)
            bias_first = beta1 * bias_first + (1.0 - beta1) * grad_bias
            bias_second = beta2 * bias_second + (1.0 - beta2) * (grad_bias**2)

            first_hat = first_moment / (1.0 - beta1**step)
            second_hat = second_moment / (1.0 - beta2**step)
            bias_first_hat = bias_first / (1.0 - beta1**step)
            bias_second_hat = bias_second / (1.0 - beta2**step)

            weights -= learning_rate * first_hat / (np.sqrt(second_hat) + eps)
            bias -= learning_rate * bias_first_hat / (math.sqrt(bias_second_hat) + eps)

        full_probabilities = sigmoid(X @ weights + bias)
        loss = -float(
            np.mean(
                y * np.log(full_probabilities + 1e-12)
                + (1.0 - y) * np.log(1.0 - full_probabilities + 1e-12)
            )
        ) + 0.5 * l2 * float(np.sum(weights * weights))
        losses.append(loss)

    return weights, bias, losses


def roc_auc_score(y_true: np.ndarray, scores: np.ndarray) -> float:
    y_true = y_true.astype(int)
    positives = int(np.sum(y_true == 1))
    negatives = int(np.sum(y_true == 0))
    if positives == 0 or negatives == 0:
        return float("nan")

    order = np.argsort(scores)
    sorted_scores = scores[order]
    ranks = np.empty(len(scores), dtype=float)

    start = 0
    while start < len(scores):
        end = start + 1
        while end < len(scores) and sorted_scores[end] == sorted_scores[start]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = average_rank
        start = end

    positive_rank_sum = float(np.sum(ranks[y_true == 1]))
    return (positive_rank_sum - positives * (positives + 1) / 2.0) / (
        positives * negatives
    )


def average_precision_score(y_true: np.ndarray, scores: np.ndarray) -> float:
    y_true = y_true.astype(int)
    positives = int(np.sum(y_true == 1))
    if positives == 0:
        return float("nan")

    order = np.argsort(-scores)
    sorted_true = y_true[order]
    cumulative_true = np.cumsum(sorted_true)
    precision = cumulative_true / (np.arange(len(sorted_true)) + 1)
    return float(np.sum(precision * sorted_true) / positives)


def binary_metrics(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float]:
    predictions = (scores >= threshold).astype(int)
    y_true = y_true.astype(int)
    tp = int(np.sum((predictions == 1) & (y_true == 1)))
    fp = int(np.sum((predictions == 1) & (y_true == 0)))
    tn = int(np.sum((predictions == 0) & (y_true == 0)))
    fn = int(np.sum((predictions == 0) & (y_true == 1)))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    accuracy = (tp + tn) / len(y_true) if len(y_true) else 0.0
    return {
        "threshold": float(threshold),
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": float(precision),
        "recall": float(recall),
        "specificity": float(specificity),
        "f1": float(f1),
        "accuracy": float(accuracy),
    }


def best_f1_threshold_metrics(y_true: np.ndarray, scores: np.ndarray) -> dict[str, float]:
    thresholds = np.unique(np.quantile(scores, np.linspace(0.01, 0.99, 199)))
    best = binary_metrics(y_true, scores, threshold=0.5)
    for threshold in thresholds:
        candidate = binary_metrics(y_true, scores, threshold=float(threshold))
        if candidate["f1"] > best["f1"]:
            best = candidate
    return best


def predict_scores(latlon: np.ndarray, model: dict[str, Any]) -> np.ndarray:
    X, _ = make_features(latlon, model["params"], fit_scaler=False)
    weights = np.array(model["weights"], dtype=float)
    bias = float(model["bias"])
    return sigmoid(X @ weights + bias)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_prediction_csv(path: Path, latlon: np.ndarray, scores: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "latitude": latlon[:, 0],
            "longitude": latlon[:, 1],
            "landslide_susceptibility": scores,
        }
    ).to_csv(path, index=False)
