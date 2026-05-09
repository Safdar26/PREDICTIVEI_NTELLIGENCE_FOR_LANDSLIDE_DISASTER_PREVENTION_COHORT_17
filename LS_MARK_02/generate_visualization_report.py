#!/usr/bin/env python3
"""Generate a self-contained train/test visualization report for the project."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


RED = "#c9453c"
BLUE = "#2f6f9f"
GREEN = "#2d7d46"
GOLD = "#c69214"
INK = "#1f2933"
MUTED = "#6b7280"
GRID = "#d9dee5"
PAPER = "#ffffff"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default=Path("data/processed/landslide_inventory.csv"), type=Path)
    parser.add_argument("--spatial-metrics", default=Path("reports/spatial_baseline_metrics.json"), type=Path)
    parser.add_argument("--spatial-eval", default=Path("reports/spatial_baseline_eval_predictions.csv"), type=Path)
    parser.add_argument("--spatial-grid", default=Path("reports/spatial_baseline_susceptibility_grid.csv"), type=Path)
    parser.add_argument("--external-metrics", default=Path("reports/external_api_model_metrics.json"), type=Path)
    parser.add_argument("--external-eval", default=Path("reports/external_api_eval_predictions.csv"), type=Path)
    parser.add_argument("--external-model", default=Path("models/external_api_landslide_model.json"), type=Path)
    parser.add_argument("--out", default=Path("reports/train_test_visualization_report.html"), type=Path)
    parser.add_argument("--summary-out", default=Path("reports/train_test_visualization_summary.md"), type=Path)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: Any) -> str:
    return html.escape(str(value))


def fmt(value: Any, digits: int = 3) -> str:
    if value is None:
        return "NA"
    try:
        if pd.isna(value):
            return "NA"
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) >= 1000:
        return f"{number:,.0f}"
    return f"{number:.{digits}f}"


def metric_value(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def chart_frame(width: int, height: int, title: str, body: str) -> str:
    return (
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{esc(title)}" class="chart">'
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="8" fill="{PAPER}" />'
        f'<text x="18" y="28" class="chart-title">{esc(title)}</text>'
        f"{body}</svg>"
    )


def axis_grid(x0: int, y0: int, width: int, height: int, x_ticks: int = 4, y_ticks: int = 4) -> str:
    parts = []
    for i in range(x_ticks + 1):
        x = x0 + width * i / x_ticks
        parts.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y0 + height}" class="grid" />')
    for i in range(y_ticks + 1):
        y = y0 + height * i / y_ticks
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0 + width}" y2="{y:.1f}" class="grid" />')
    parts.append(f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" fill="none" class="axis" />')
    return "".join(parts)


def path_from_xy(xs: np.ndarray, ys: np.ndarray, x0: int, y0: int, width: int, height: int) -> str:
    if len(xs) == 0:
        return ""
    points = []
    for x, y in zip(xs, ys):
        px = x0 + float(x) * width
        py = y0 + (1.0 - float(y)) * height
        points.append(f"{px:.1f},{py:.1f}")
    return " ".join(points)


def downsample_curve(xs: np.ndarray, ys: np.ndarray, max_points: int = 900) -> tuple[np.ndarray, np.ndarray]:
    if len(xs) <= max_points:
        return xs, ys
    indices = np.linspace(0, len(xs) - 1, max_points).round().astype(int)
    indices = np.unique(indices)
    return xs[indices], ys[indices]


def roc_points(df: pd.DataFrame, split: str) -> tuple[np.ndarray, np.ndarray]:
    subset = df[df["split"].eq(split)].copy()
    y = subset["label"].astype(int).to_numpy()
    scores = subset["landslide_susceptibility"].astype(float).to_numpy()
    if len(y) == 0 or y.sum() == 0 or (len(y) - y.sum()) == 0:
        return np.array([]), np.array([])
    order = np.argsort(-scores)
    y = y[order]
    tp = np.cumsum(y == 1)
    fp = np.cumsum(y == 0)
    tpr = np.r_[0.0, tp / max(tp[-1], 1), 1.0]
    fpr = np.r_[0.0, fp / max(fp[-1], 1), 1.0]
    return fpr, tpr


def pr_points(df: pd.DataFrame, split: str) -> tuple[np.ndarray, np.ndarray]:
    subset = df[df["split"].eq(split)].copy()
    y = subset["label"].astype(int).to_numpy()
    scores = subset["landslide_susceptibility"].astype(float).to_numpy()
    if len(y) == 0 or y.sum() == 0:
        return np.array([]), np.array([])
    order = np.argsort(-scores)
    y = y[order]
    tp = np.cumsum(y == 1)
    precision = tp / (np.arange(len(y)) + 1)
    recall = tp / max(tp[-1], 1)
    return np.r_[0.0, recall], np.r_[1.0, precision]


def curve_chart(title: str, df: pd.DataFrame, kind: str) -> str:
    width, height = 560, 380
    x0, y0, cw, ch = 58, 54, 470, 270
    body = [axis_grid(x0, y0, cw, ch)]
    curves = [("train", BLUE), ("test", RED)]
    for split, color in curves:
        if kind == "roc":
            xs, ys = roc_points(df, split)
            x_label, y_label = "False positive rate", "True positive rate"
        else:
            xs, ys = pr_points(df, split)
            x_label, y_label = "Recall", "Precision"
        xs, ys = downsample_curve(xs, ys)
        points = path_from_xy(xs, ys, x0, y0, cw, ch)
        if points:
            body.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.6" />')
    body.append(f'<text x="{x0 + cw / 2}" y="{height - 24}" text-anchor="middle" class="axis-label">{x_label}</text>')
    body.append(f'<text x="18" y="{y0 + ch / 2}" transform="rotate(-90 18 {y0 + ch / 2})" text-anchor="middle" class="axis-label">{y_label}</text>')
    body.append(legend([(BLUE, "train"), (RED, "test")], x0 + 8, y0 + ch + 20))
    return chart_frame(width, height, title, "".join(body))


def legend(items: list[tuple[str, str]], x: float, y: float) -> str:
    parts = []
    for idx, (color, label) in enumerate(items):
        px = x + idx * 88
        parts.append(f'<rect x="{px:.1f}" y="{y - 10:.1f}" width="12" height="12" fill="{color}" rx="2" />')
        parts.append(f'<text x="{px + 18:.1f}" y="{y:.1f}" class="legend">{esc(label)}</text>')
    return "".join(parts)


def score_histogram(title: str, df: pd.DataFrame, split: str) -> str:
    width, height = 560, 360
    x0, y0, cw, ch = 54, 52, 472, 250
    bins = np.linspace(0.0, 1.0, 21)
    subset = df[df["split"].eq(split)]
    positives = subset[subset["label"].eq(1)]["landslide_susceptibility"].astype(float)
    negatives = subset[subset["label"].eq(0)]["landslide_susceptibility"].astype(float)
    pos_counts, _ = np.histogram(positives, bins=bins)
    neg_counts, _ = np.histogram(negatives, bins=bins)
    ymax = max(int(pos_counts.max(initial=0)), int(neg_counts.max(initial=0)), 1)
    body = [axis_grid(x0, y0, cw, ch)]
    bar_w = cw / (len(bins) - 1)
    for idx, (pos_count, neg_count) in enumerate(zip(pos_counts, neg_counts)):
        x = x0 + idx * bar_w
        neg_h = ch * neg_count / ymax
        pos_h = ch * pos_count / ymax
        body.append(f'<rect x="{x + 2:.1f}" y="{y0 + ch - neg_h:.1f}" width="{bar_w - 4:.1f}" height="{neg_h:.1f}" fill="{BLUE}" opacity="0.58" />')
        body.append(f'<rect x="{x + 2:.1f}" y="{y0 + ch - pos_h:.1f}" width="{bar_w - 4:.1f}" height="{pos_h:.1f}" fill="{RED}" opacity="0.58" />')
    body.append(f'<text x="{x0 + cw / 2}" y="{height - 22}" text-anchor="middle" class="axis-label">Predicted susceptibility score</text>')
    body.append(f'<text x="20" y="{y0 + ch / 2}" transform="rotate(-90 20 {y0 + ch / 2})" text-anchor="middle" class="axis-label">Rows</text>')
    body.append(legend([(RED, "landslide"), (BLUE, "background")], x0 + 8, y0 + ch + 20))
    return chart_frame(width, height, title, "".join(body))


def metric_bar_chart(spatial: dict[str, Any], external: dict[str, Any]) -> str:
    width, height = 660, 360
    x0, y0, cw, ch = 72, 54, 540, 236
    metrics = [
        ("Train ROC-AUC", metric_value(spatial, "train_roc_auc"), metric_value(external, "train_roc_auc")),
        ("Test ROC-AUC", metric_value(spatial, "test_roc_auc"), metric_value(external, "test_roc_auc")),
        ("Train AP", metric_value(spatial, "train_average_precision"), metric_value(external, "train_average_precision")),
        ("Test AP", metric_value(spatial, "test_average_precision"), metric_value(external, "test_average_precision")),
    ]
    body = [axis_grid(x0, y0, cw, ch)]
    group_w = cw / len(metrics)
    bar_w = group_w * 0.28
    for idx, (label, spatial_value, external_value) in enumerate(metrics):
        base_x = x0 + idx * group_w + group_w * 0.22
        for offset, value, color in [(0, spatial_value, BLUE), (bar_w + 5, external_value, GOLD)]:
            if value is None:
                continue
            h = ch * max(0.0, min(1.0, value))
            body.append(f'<rect x="{base_x + offset:.1f}" y="{y0 + ch - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{color}" rx="3" />')
            body.append(f'<text x="{base_x + offset + bar_w / 2:.1f}" y="{y0 + ch - h - 6:.1f}" text-anchor="middle" class="tiny">{fmt(value, 2)}</text>')
        body.append(f'<text x="{x0 + idx * group_w + group_w / 2:.1f}" y="{height - 36}" text-anchor="middle" class="tick">{esc(label)}</text>')
    body.append(legend([(BLUE, "spatial"), (GOLD, "API")], x0 + 8, y0 + ch + 24))
    return chart_frame(width, height, "Train/Test Model Metrics", "".join(body))


def loss_chart(title: str, losses: list[float]) -> str:
    width, height = 560, 320
    x0, y0, cw, ch = 54, 52, 472, 210
    body = [axis_grid(x0, y0, cw, ch)]
    if losses:
        values = np.array(losses, dtype=float)
        ymin = float(values.min())
        ymax = float(values.max())
        if ymax == ymin:
            ymax = ymin + 1.0
        xs = np.linspace(0.0, 1.0, len(values))
        ys = (values - ymin) / (ymax - ymin)
        points = path_from_xy(xs, ys, x0, y0, cw, ch)
        body.append(f'<polyline points="{points}" fill="none" stroke="{GREEN}" stroke-width="2.6" />')
        body.append(f'<text x="{x0}" y="{y0 + ch + 22}" class="tiny">min {fmt(ymin, 4)} / max {fmt(ymax, 4)}</text>')
    body.append(f'<text x="{x0 + cw / 2}" y="{height - 22}" text-anchor="middle" class="axis-label">Epoch</text>')
    return chart_frame(width, height, title, "".join(body))


def confusion_matrix_chart(title: str, metrics: dict[str, Any], key: str = "test_best_f1_threshold_metrics") -> str:
    values = metrics.get(key, {})
    width, height = 420, 360
    x0, y0, cell = 110, 72, 112
    tn = int(values.get("true_negative", 0))
    fp = int(values.get("false_positive", 0))
    fn = int(values.get("false_negative", 0))
    tp = int(values.get("true_positive", 0))
    cells = [
        (0, 0, tn, "TN", BLUE),
        (1, 0, fp, "FP", GOLD),
        (0, 1, fn, "FN", GOLD),
        (1, 1, tp, "TP", RED),
    ]
    max_count = max(tn, fp, fn, tp, 1)
    body = []
    for cx, cy, count, label, color in cells:
        opacity = 0.22 + 0.72 * count / max_count
        x = x0 + cx * cell
        y = y0 + cy * cell
        body.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}" opacity="{opacity:.2f}" stroke="#ffffff" stroke-width="3" />')
        body.append(f'<text x="{x + cell / 2}" y="{y + 46}" text-anchor="middle" class="cell-label">{label}</text>')
        body.append(f'<text x="{x + cell / 2}" y="{y + 76}" text-anchor="middle" class="cell-count">{count:,}</text>')
    body.append(f'<text x="{x0 + cell}" y="{y0 - 16}" text-anchor="middle" class="axis-label">Predicted class</text>')
    body.append(f'<text x="{x0 - 54}" y="{y0 + cell}" transform="rotate(-90 {x0 - 54} {y0 + cell})" text-anchor="middle" class="axis-label">Actual class</text>')
    body.append(f'<text x="{x0 + cell}" y="{height - 24}" text-anchor="middle" class="tiny">threshold {fmt(values.get("threshold"), 4)} / F1 {fmt(values.get("f1"), 3)}</text>')
    return chart_frame(width, height, title, "".join(body))


def scatter_map(title: str, df: pd.DataFrame, max_points: int = 4500) -> str:
    width, height = 560, 520
    x0, y0, cw, ch = 48, 54, 470, 390
    plot_df = df.dropna(subset=["latitude", "longitude", "label"]).copy()
    if len(plot_df) > max_points:
        plot_df = plot_df.sample(n=max_points, random_state=42)
    min_lon, max_lon = plot_df["longitude"].min(), plot_df["longitude"].max()
    min_lat, max_lat = plot_df["latitude"].min(), plot_df["latitude"].max()
    body = [axis_grid(x0, y0, cw, ch)]
    for label, color, radius in [(0, BLUE, 1.4), (1, RED, 1.8)]:
        subset = plot_df[plot_df["label"].eq(label)]
        for _, row in subset.iterrows():
            x = x0 + (row["longitude"] - min_lon) / max(max_lon - min_lon, 1e-9) * cw
            y = y0 + (1.0 - (row["latitude"] - min_lat) / max(max_lat - min_lat, 1e-9)) * ch
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" opacity="0.45" />')
    body.append(legend([(RED, "landslide"), (BLUE, "background")], x0 + 8, y0 + ch + 26))
    body.append(f'<text x="{x0 + cw / 2}" y="{height - 28}" text-anchor="middle" class="axis-label">Longitude</text>')
    body.append(f'<text x="18" y="{y0 + ch / 2}" transform="rotate(-90 18 {y0 + ch / 2})" text-anchor="middle" class="axis-label">Latitude</text>')
    return chart_frame(width, height, title, "".join(body))


def horizontal_bar_chart(title: str, rows: list[tuple[str, float]], positive_negative: bool = False) -> str:
    width, height = 680, max(280, 58 + len(rows) * 28)
    x0, y0, cw = 245, 48, 382
    max_abs = max([abs(value) for _, value in rows] + [1e-9])
    body = []
    zero_x = x0 + (cw / 2 if positive_negative else 0)
    if positive_negative:
        body.append(f'<line x1="{zero_x}" y1="{y0 - 8}" x2="{zero_x}" y2="{y0 + len(rows) * 28}" stroke="{GRID}" stroke-width="1" />')
    for idx, (label, value) in enumerate(rows):
        y = y0 + idx * 28
        if positive_negative:
            length = abs(value) / max_abs * (cw / 2 - 6)
            x = zero_x if value >= 0 else zero_x - length
            color = GREEN if value >= 0 else RED
        else:
            length = value / max_abs * cw
            x = x0
            color = BLUE
        body.append(f'<text x="{x0 - 10}" y="{y + 15}" text-anchor="end" class="tick">{esc(label)}</text>')
        body.append(f'<rect x="{x:.1f}" y="{y + 3}" width="{length:.1f}" height="17" fill="{color}" rx="3" />')
        body.append(f'<text x="{x + length + 6:.1f}" y="{y + 16}" class="tiny">{fmt(value, 3)}</text>')
    return chart_frame(width, height, title, "".join(body))


def state_chart(inventory: pd.DataFrame) -> str:
    state_col = "state_normalized" if "state_normalized" in inventory.columns else "state"
    counts = inventory[state_col].fillna("Unknown").value_counts().head(12)
    rows = [(str(index), float(value)) for index, value in counts.items()]
    return horizontal_bar_chart("Inventory Records By State/UT", rows)


def table_html(headers: list[str], rows: list[list[Any]]) -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{esc(value)}</td>" for value in row) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def metric_cards(spatial: dict[str, Any], external: dict[str, Any]) -> str:
    cards = [
        ("Spatial Train ROC-AUC", metric_value(spatial, "train_roc_auc")),
        ("Spatial Test ROC-AUC", metric_value(spatial, "test_roc_auc")),
        ("Spatial Test AP", metric_value(spatial, "test_average_precision")),
        ("API Train ROC-AUC", metric_value(external, "train_roc_auc")),
        ("API Test ROC-AUC", metric_value(external, "test_roc_auc")),
        ("API Test AP", metric_value(external, "test_average_precision")),
    ]
    return '<div class="cards">' + "".join(
        f'<div class="metric-card"><div class="metric-label">{esc(label)}</div><div class="metric-value">{fmt(value)}</div></div>'
        for label, value in cards
    ) + "</div>"


def feature_weight_chart(model: dict[str, Any]) -> str:
    preprocessing = model.get("preprocessing", {})
    columns = preprocessing.get("feature_columns", [])
    weights = model.get("weights", [])
    rows = []
    for column, weight in zip(columns, weights):
        rows.append((column, float(weight)))
    rows.sort(key=lambda item: abs(item[1]), reverse=True)
    return horizontal_bar_chart("External API Model Feature Weights", rows[:16], positive_negative=True)


def top_grid_table(path: Path) -> str:
    if not path.exists():
        return "<p>Susceptibility grid is not available.</p>"
    grid = pd.read_csv(path)
    if "landslide_susceptibility" not in grid.columns:
        return "<p>Grid file does not contain susceptibility scores.</p>"
    top = grid.nlargest(12, "landslide_susceptibility")
    rows = [
        [fmt(row.latitude, 4), fmt(row.longitude, 4), fmt(row.landslide_susceptibility, 4)]
        for row in top.itertuples(index=False)
    ]
    return table_html(["Latitude", "Longitude", "Score"], rows)


def model_summary_table(spatial: dict[str, Any], external: dict[str, Any]) -> str:
    rows = [
        ["Spatial baseline", spatial.get("train_rows", "NA"), spatial.get("test_rows", "NA"), fmt(spatial.get("test_roc_auc")), fmt(spatial.get("test_average_precision"))],
        ["External API model", external.get("train_rows", "NA"), external.get("test_rows", "NA"), fmt(external.get("test_roc_auc")), fmt(external.get("test_average_precision"))],
    ]
    return table_html(["Model", "Train rows", "Test rows", "Test ROC-AUC", "Test AP"], rows)


def build_html(args: argparse.Namespace) -> str:
    spatial_metrics = read_json(args.spatial_metrics)
    external_metrics = read_json(args.external_metrics)
    external_model = read_json(args.external_model)
    inventory = pd.read_csv(args.inventory) if args.inventory.exists() else pd.DataFrame()
    spatial_eval = pd.read_csv(args.spatial_eval) if args.spatial_eval.exists() else pd.DataFrame()
    external_eval = pd.read_csv(args.external_eval) if args.external_eval.exists() else pd.DataFrame()

    sections = []
    sections.append("<section><h2>Model Scorecard</h2>" + metric_cards(spatial_metrics, external_metrics) + model_summary_table(spatial_metrics, external_metrics) + "</section>")
    sections.append("<section><h2>Metric Comparison</h2>" + metric_bar_chart(spatial_metrics, external_metrics) + "</section>")
    if not inventory.empty:
        sections.append("<section><h2>Inventory Overview</h2>" + state_chart(inventory) + "</section>")
    if not spatial_eval.empty:
        sections.append(
            "<section><h2>Spatial Baseline Train/Test Visuals</h2>"
            '<div class="grid2">'
            + curve_chart("Spatial ROC Curve", spatial_eval, "roc")
            + curve_chart("Spatial Precision-Recall Curve", spatial_eval, "pr")
            + score_histogram("Spatial Train Score Distribution", spatial_eval, "train")
            + score_histogram("Spatial Test Score Distribution", spatial_eval, "test")
            + confusion_matrix_chart("Spatial Test Confusion Matrix", spatial_metrics)
            + scatter_map("Spatial Training Points Map", spatial_eval)
            + loss_chart("Spatial Training Loss", spatial_metrics.get("loss_history", []))
            + "</div></section>"
        )
    if not external_eval.empty:
        sections.append(
            "<section><h2>External API Model Train/Test Visuals</h2>"
            '<div class="grid2">'
            + curve_chart("External API ROC Curve", external_eval, "roc")
            + curve_chart("External API Precision-Recall Curve", external_eval, "pr")
            + score_histogram("External API Train Score Distribution", external_eval, "train")
            + score_histogram("External API Test Score Distribution", external_eval, "test")
            + confusion_matrix_chart("External API Test Confusion Matrix", external_metrics)
            + scatter_map("External API Training Points Map", external_eval)
            + loss_chart("External API Training Loss", external_metrics.get("loss_history", []))
            + "</div></section>"
        )
    if external_model:
        sections.append("<section><h2>External API Feature Weights</h2>" + feature_weight_chart(external_model) + "</section>")
    sections.append("<section><h2>Top Spatial Grid Scores</h2>" + top_grid_table(args.spatial_grid) + "</section>")
    sections.append(
        "<section><h2>Notes</h2>"
        "<ul>"
        "<li>The spatial baseline uses coordinate-only radial-basis features and pseudo-background points.</li>"
        "<li>The API model uses NASA POWER and USGS features, with optional OpenWeather features when a key is present.</li>"
        "<li>Current API model metrics come from a small live API sample, so they validate the pipeline more than final model quality.</li>"
        "<li>Use spatial or regional holdout validation for future scaled runs.</li>"
        "</ul></section>"
    )

    css = """
    body { margin: 0; font-family: Inter, Arial, sans-serif; color: #1f2933; background: #f4f6f8; }
    header { background: #164e63; color: #ffffff; padding: 32px 42px; }
    main { max-width: 1240px; margin: 0 auto; padding: 28px; }
    section { background: #ffffff; border: 1px solid #d9dee5; border-radius: 8px; margin: 0 0 24px; padding: 22px; }
    h1 { margin: 0 0 8px; font-size: 30px; }
    h2 { margin: 0 0 18px; font-size: 22px; }
    p, li { line-height: 1.55; }
    table { border-collapse: collapse; width: 100%; margin-top: 16px; font-size: 14px; }
    th, td { border-bottom: 1px solid #e5e9ef; padding: 9px 8px; text-align: left; }
    th { background: #eef2f6; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(175px, 1fr)); gap: 12px; margin-bottom: 18px; }
    .metric-card { border: 1px solid #d9dee5; border-radius: 8px; padding: 14px; background: #f9fafb; }
    .metric-label { color: #6b7280; font-size: 13px; }
    .metric-value { color: #1f2933; font-size: 28px; font-weight: 750; margin-top: 5px; }
    .grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 18px; }
    .chart { width: 100%; height: auto; border: 1px solid #e5e9ef; border-radius: 8px; background: #ffffff; }
    .chart-title { font-size: 17px; font-weight: 700; fill: #1f2933; }
    .axis { stroke: #9aa5b1; stroke-width: 1; }
    .grid { stroke: #d9dee5; stroke-width: 1; }
    .axis-label, .legend, .tick { fill: #4b5563; font-size: 12px; }
    .tiny { fill: #4b5563; font-size: 10.5px; }
    .cell-label { fill: #ffffff; font-size: 19px; font-weight: 750; }
    .cell-count { fill: #ffffff; font-size: 18px; font-weight: 700; }
    """
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\" />"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />"
        "<title>Landslide Train/Test Visualization Report</title>"
        f"<style>{css}</style></head><body>"
        "<header><h1>Landslide Train/Test Visualization Report</h1>"
        "<p>Inventory extraction, spatial baseline, and external API model diagnostics.</p></header>"
        "<main>"
        + "".join(sections)
        + "</main></body></html>"
    )


def build_summary(args: argparse.Namespace) -> str:
    spatial_metrics = read_json(args.spatial_metrics)
    external_metrics = read_json(args.external_metrics)
    return "\n".join(
        [
            "# Train/Test Visualization Summary",
            "",
            f"- HTML report: `{args.out}`",
            f"- Spatial train ROC-AUC: {fmt(spatial_metrics.get('train_roc_auc'))}",
            f"- Spatial test ROC-AUC: {fmt(spatial_metrics.get('test_roc_auc'))}",
            f"- Spatial test average precision: {fmt(spatial_metrics.get('test_average_precision'))}",
            f"- External API train ROC-AUC: {fmt(external_metrics.get('train_roc_auc'))}",
            f"- External API test ROC-AUC: {fmt(external_metrics.get('test_roc_auc'))}",
            f"- External API test average precision: {fmt(external_metrics.get('test_average_precision'))}",
            "",
            "Generated charts include metric bars, ROC curves, precision-recall curves,",
            "score histograms, confusion matrices, train/test point maps, loss curves,",
            "external feature weights, and top spatial susceptibility grid points.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_html(args), encoding="utf-8")
    args.summary_out.write_text(build_summary(args), encoding="utf-8")
    print(f"Wrote visualization report to {args.out}")
    print(f"Wrote summary to {args.summary_out}")


if __name__ == "__main__":
    main()
