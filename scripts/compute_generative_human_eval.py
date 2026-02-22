#!/usr/bin/env python3
"""
Compute Generative (human eval %) vs human labels per pattern.

Uses the current agents from src.app: create_app(pattern) builds the pipeline
with factor agents and combiner from src/app.py. Full CoT and Full FCoT use
src/cot_prompt.py and src/fcot_prompt.py respectively. Re-run this script after
changing prompts or app logic to refresh data/generative_human_eval_table.csv.
"""

import argparse
import asyncio
import sys
from pathlib import Path

import pandas as pd

_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))
try:
    from dotenv import load_dotenv
    load_dotenv(_project_root / ".env")
except ImportError:
    pass

from src.app import create_app, PATTERNS
from src.run import run

PATTERN_DISPLAY = {
    "simple_prompt": "Simple Prompt",
    "function_calling": "Function Calling",
    "simple_plus_function": "Simple + Function",
    "basic_cot": "Basic Chain of Thought",
    "cot": "Full CoT",
    "fcot": "Full FCoT",
    "complex_prompt": "Complex Prompt",
}

FACTOR_MAP = [
    ("toxicity", "toxicity_level"),
    ("title_vs_body", "title_body_alignment"),
    ("clickbait", "clickbait_level"),
    ("political_affiliation", "political_affiliation_bias"),
    ("sentiment", "sentiment_bias"),
    ("sensationalism", "sensationalism"),
]

FACTOR_DISPLAY = {
    "toxicity": "Toxicity",
    "title_vs_body": "Title vs. Body",
    "clickbait": "Clickbait",
    "political_affiliation": "Political Affiliation",
    "sentiment": "Sentiment Analysis",
    "sensationalism": "Sensationalism",
}


def load_labeled_articles(csv_path: Path, sample=None) -> pd.DataFrame:
    """Load articles with human labels. Truncate body_text if needed to avoid token limits."""
    df = pd.read_csv(csv_path)
    label_cols = [c for c, _ in FACTOR_MAP]
    for col in label_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=label_cols)
    if sample:
        df = df.head(sample)
    if "body_text" in df.columns:
        df["body_text"] = df["body_text"].fillna("").astype(str).str.slice(0, 8000)
    if "title" not in df.columns:
        df["title"] = ""
    if "url" not in df.columns:
        df["url"] = ""
    return df.reset_index(drop=True)


def _run_sync(article: dict, pattern: str = None) -> dict:
    """Run the async pipeline in a fresh event loop (for use in scripts)."""
    app_instance = create_app(pattern=pattern) if pattern else None
    return asyncio.run(
        run(
            article_title=article["title"],
            article_content=article["body_text"],
            article_url=article.get("url", ""),
            predictive_scores=None,
            app_instance=app_instance,
        )
    )


def compute_metrics(pred: list[float], truth: list[float]) -> dict:
    """Compute Pearson correlation, MAE, % within ±2, and 100 - normalized_MAE."""
    import numpy as np

    pred = np.array(pred, dtype=float)
    truth = np.array(truth, dtype=float)
    valid = np.isfinite(pred) & np.isfinite(truth)
    pred = pred[valid]
    truth = truth[valid]
    n = len(pred)
    if n == 0:
        return {"pearson": None, "mae": None, "pct_within_2": None, "human_eval_pct": None}

    if n > 1 and pred.std() > 0 and truth.std() > 0:
        pearson = float(np.corrcoef(pred, truth)[0, 1])
    else:
        pearson = None

    mae = float(np.abs(pred - truth).mean())
    within_2 = np.sum(np.abs(pred - truth) <= 2) / n * 100
    human_eval_pct = 100 - (mae / 10) * 100
    human_eval_pct = max(0, min(100, human_eval_pct))

    return {
        "pearson": pearson,
        "mae": mae,
        "pct_within_2": within_2,
        "human_eval_pct": round(human_eval_pct, 1),
    }


def run_pattern_on_articles(df: pd.DataFrame, pattern: str) -> dict[str, list[float]]:
    """Run one pattern on all articles; return predictions per factor."""
    predictions = {csv_col: [] for csv_col, _ in FACTOR_MAP}
    for i, row in df.iterrows():
        try:
            result = _run_sync(row.to_dict(), pattern=pattern)
            fs = result.get("factor_scores") or {}
            for csv_col, model_key in FACTOR_MAP:
                v = fs.get(model_key)
                if v is not None:
                    try:
                        predictions[csv_col].append(float(v))
                    except (TypeError, ValueError):
                        predictions[csv_col].append(float("nan"))
                else:
                    predictions[csv_col].append(float("nan"))
        except Exception as e:
            print(f"    Article {i} failed: {e}", flush=True)
            for csv_col, _ in FACTOR_MAP:
                predictions[csv_col].append(float("nan"))
    return predictions


def main():
    parser = argparse.ArgumentParser(description="Compute Generative (human eval %) vs human labels per pattern")
    parser.add_argument("--sample", type=int, default=10, help="Number of articles to evaluate per pattern (default: 10)")
    parser.add_argument("--csv", type=Path, default=None, help="Path to labeled CSV")
    parser.add_argument("--pattern", type=str, default=None, help="Run single pattern only (default: all)")
    args = parser.parse_args()

    csv_path = args.csv or (_project_root / "data" / "articles_labeled_human_scored_v2.csv")
    if not csv_path.exists():
        print(f"Error: {csv_path} not found", flush=True)
        sys.exit(1)

    patterns_to_run = [args.pattern] if args.pattern else PATTERNS
    if args.pattern and args.pattern not in PATTERNS:
        print(f"Error: pattern must be one of {PATTERNS}", flush=True)
        sys.exit(1)

    df = load_labeled_articles(csv_path, sample=args.sample)
    print("Using create_app() from src.app (current CoT/FCoT from cot_prompt.py and fcot_prompt.py).", flush=True)
    print(f"Loaded {len(df)} articles. Running {len(patterns_to_run)} patterns...", flush=True)

    compact_rows = []
    all_metrics = []

    for pattern in patterns_to_run:
        display = PATTERN_DISPLAY.get(pattern, pattern)
        print(f"  Running {display}...", flush=True)
        predictions = run_pattern_on_articles(df, pattern)
        row_pct = {"Pattern": display}
        for csv_col, _ in FACTOR_MAP:
            pred = predictions[csv_col]
            truth = df[csv_col].astype(float).tolist()
            m = compute_metrics(pred, truth)
            row_pct[FACTOR_DISPLAY[csv_col]] = m["human_eval_pct"]
            all_metrics.append({
                "Pattern": display,
                "Factor": FACTOR_DISPLAY[csv_col],
                "Pearson": m["pearson"],
                "MAE": m["mae"],
                "% within ±2": m["pct_within_2"],
                "Generative (human eval %)": m["human_eval_pct"],
            })
        compact_rows.append(row_pct)

    print("\n" + "=" * 80, flush=True)
    print("Table format (Pattern × Factor → Generative human eval %):", flush=True)
    print("=" * 80, flush=True)
    compact_cols = ["Toxicity", "Title vs. Body", "Clickbait", "Political Affiliation", "Sentiment Analysis", "Sensationalism"]
    compact_df = pd.DataFrame(compact_rows)
    compact_df = compact_df[["Pattern"] + compact_cols]
    print(compact_df.to_string(index=False), flush=True)

    metrics_path = _project_root / "data" / "generative_human_eval_results.csv"
    compact_path = _project_root / "data" / "generative_human_eval_table.csv"
    pd.DataFrame(all_metrics).to_csv(metrics_path, index=False)
    compact_df.to_csv(compact_path, index=False)
    print(f"\nDetailed results saved to {metrics_path}", flush=True)
    print(f"Compact table (one row per pattern) saved to {compact_path}", flush=True)


if __name__ == "__main__":
    main()
