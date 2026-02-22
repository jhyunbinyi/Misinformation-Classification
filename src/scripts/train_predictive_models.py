"""
Train the six predictive models and save to data/models/*.joblib.
Run from project root: python src/scripts/train_predictive_models.py
"""

import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Project root (src/scripts/ -> src/ -> root)
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data"
MODELS_DIR = ROOT / "data" / "models"

TSV_COLUMNS = [
    "id", "label", "statement", "subjects", "speaker", "speaker_job_title",
    "state_info", "party_affiliation", "barely_true_counts", "false_counts",
    "half_true_counts", "mostly_true_counts", "pants_on_fire_counts",
    "context", "justification", "json_file_id",
]


def _preprocess(text: str) -> str:
    return (str(text).lower().strip() if text else "")[:100_000]


def _load_tsv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", header=None, on_bad_lines="skip")
    df = df.drop(df.columns[0], axis=1)
    df.columns = TSV_COLUMNS[: len(df.columns)]
    df["statement"] = df["statement"].astype(str).fillna("").str.strip()
    df["justification"] = df.get("justification", pd.Series([""] * len(df))).astype(str).fillna("")
    return df.dropna(subset=["statement"])


def train_clickbait():
    path = DATA / "clickbait" / "train1.csv"
    if not path.exists():
        print(f"[SKIP] Clickbait: {path} not found")
        return None
    df = pd.read_csv(path)
    text_col = "headline" if "headline" in df.columns else df.columns[0]
    label_col = "clickbait" if "clickbait" in df.columns else df.columns[1]
    X = [ _preprocess(t) for t in df[text_col] ]
    y = df[label_col].astype(int).values
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, max_features=20_000)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(X, y)
    return pipe


def train_sensationalism():
    path = DATA / "tsv" / "train2.tsv"
    if not path.exists():
        print(f"[SKIP] Sensationalism: {path} not found")
        return None
    df = _load_tsv(path)
    X = [ _preprocess(t) for t in df["statement"] ]
    # Heuristic: false / pants-fire -> sensational (1)
    label_map = {"false": 1, "pants-fire": 1, "barely-true": 0, "half-true": 0, "mostly-true": 0, "true": 0}
    y = df["label"].str.strip().str.lower().map(lambda v: label_map.get(v, 0)).values
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, max_features=20_000)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(X, y)
    return pipe


def train_title_vs_body():
    path = DATA / "tsv" / "train2.tsv"
    if not path.exists():
        print(f"[SKIP] Title vs Body: {path} not found")
        return None
    df = _load_tsv(path)
    # Input: "TITLE: ... BODY: ..."; aligned = 1 if true/mostly-true
    X = [
        " TITLE_SEP ".join([_preprocess(df["statement"].iloc[i]), _preprocess(df["justification"].iloc[i])])
        for i in range(len(df))
    ]
    label_map = {"true": 1, "mostly-true": 1, "barely-true": 0, "half-true": 0, "false": 0, "pants-fire": 0}
    y = df["label"].str.strip().str.lower().map(lambda v: label_map.get(v, 0)).values
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, max_features=20_000)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(X, y)
    return pipe


def train_sentiment():
    path = DATA / "articles_labeled.csv"
    if not path.exists():
        print(f"[SKIP] Sentiment: {path} not found")
        return None
    df = pd.read_csv(path)
    if "sentiment" not in df.columns or "title" not in df.columns or "body_text" not in df.columns:
        print("[SKIP] Sentiment: missing sentiment/title/body_text columns")
        return None
    # Combine title + body for input
    titles = df["title"].astype(str).fillna("")
    bodies = df["body_text"].astype(str).fillna("")
    X = [ _preprocess(t + " " + b) for t, b in zip(titles, bodies) ]
    sent = df["sentiment"].astype(str).str.strip().str.lower()
    # Map common values to 0=neg, 1=neu, 2=pos
    sent_map = {"negative": 0, "neg": 0, "0": 0, "neutral": 1, "neu": 1, "1": 1, "positive": 2, "pos": 2, "2": 2}
    y = sent.map(lambda v: sent_map.get(v, 1)).values
    if len(np.unique(y)) < 2:
        print("[SKIP] Sentiment: insufficient class variety")
        return None
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, max_features=20_000)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(X, y)
    return pipe


def train_toxicity():
    path = DATA / "tox-new" / "train.csv"
    if not path.exists():
        print(f"[SKIP] Toxicity: {path} not found")
        return None
    df = pd.read_csv(path)
    if "comment_text" not in df.columns or "toxic" not in df.columns:
        print("[SKIP] Toxicity: missing comment_text/toxic columns")
        return None
    X = [ _preprocess(t) for t in df["comment_text"] ]
    y = df["toxic"].astype(int).values
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, max_features=20_000)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(X, y)
    return pipe


def train_political_affiliation():
    path = DATA / "pol-new" / "train_orig.txt"
    if not path.exists():
        print(f"[SKIP] Political: {path} not found")
        return None
    lines = path.read_text(encoding="utf-8", errors="ignore").strip().split("\n")
    X, y = [], []
    for line in lines:
        parts = line.split("\t", 1)
        if len(parts) != 2:
            continue
        label_str, text = parts
        try:
            label = int(label_str.strip())
        except ValueError:
            continue
        X.append(_preprocess(text))
        y.append(label)
    if len(set(y)) < 2:
        print("[SKIP] Political: insufficient class variety")
        return None
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, max_features=20_000)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    pipe.fit(X, np.array(y))
    return pipe


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    configs = [
        ("clickbait", train_clickbait, "title"),           # input: title only
        ("sensationalism", train_sensationalism, "title_content"),
        ("title_vs_body", train_title_vs_body, "title_and_body"),
        ("sentiment", train_sentiment, "title_content"),
        ("toxicity", train_toxicity, "title_content"),
        ("political_affiliation", train_political_affiliation, "title_content"),
    ]
    for name, trainer, input_kind in configs:
        try:
            pipe = trainer()
            if pipe is not None:
                out = MODELS_DIR / f"{name}.joblib"
                joblib.dump({"pipeline": pipe, "input": input_kind}, out)
                print(f"[OK] {name} -> {out}")
            else:
                print(f"[SKIP] {name} (no model)")
        except Exception as e:
            print(f"[ERR] {name}: {e}")
    print("Done.")


if __name__ == "__main__":
    main()
