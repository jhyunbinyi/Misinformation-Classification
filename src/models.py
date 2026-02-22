"""Predictive model outputs for the pipeline. Loads trained models from data/models/."""

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import joblib
except ImportError:
    joblib = None  # type: ignore[assignment]

# Default models dir: project data/models (works when run from project root or package)
_REPO_ROOT = Path(__file__).resolve().parent.parent
_MODELS_DIR = _REPO_ROOT / "data" / "models"

# Map artifact filename (stem) -> output key
_FACTOR_TO_KEY = {
    "political_affiliation": "pa_proba",
    "clickbait": "cb_proba",
    "sensationalism": "s_proba",
    "title_vs_body": "tvb_proba",
    "sentiment": "sa_proba",
    "toxicity": "t_proba",
}


def _preprocess(text: str) -> str:
    return (str(text).lower().strip() if text else "")[:100_000]


def _predict_proba(artifact: Dict[str, Any], text: str, title: str = "", body: str = "") -> Optional[List[float]]:
    pipeline = artifact.get("pipeline")
    input_kind = artifact.get("input", "title_content")
    if pipeline is None:
        return None
    if input_kind == "title":
        X = [_preprocess(title)]
    elif input_kind == "title_and_body":
        X = [" TITLE_SEP ".join([_preprocess(title), _preprocess(body)])]
    else:
        X = [_preprocess((title or "") + " " + (text or body or ""))]
    try:
        proba = pipeline.predict_proba(X)[0]
        return proba.tolist()
    except Exception:
        return None


def get_predictive_scores(
    article_title: str,
    article_content: str,
    article_url: str = "",
    models_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Return predictive model probability vectors for the article.
    Keys: pa_proba, cb_proba, s_proba, sa_proba, t_proba, tvb_proba.
    Each value is a list of class probabilities or None if the model is missing.
    """
    out: Dict[str, Any] = {}
    base_dir = Path(models_dir) if models_dir is not None else _MODELS_DIR
    if not base_dir.exists() or joblib is None:
        return {k: None for k in ["pa_proba", "cb_proba", "s_proba", "sa_proba", "t_proba", "tvb_proba"]}

    for factor, key in _FACTOR_TO_KEY.items():
        path = base_dir / f"{factor}.joblib"
        if not path.exists():
            out[key] = None
            continue
        try:
            artifact = joblib.load(path)
            proba = _predict_proba(
                artifact,
                text=article_content,
                title=article_title or "",
                body=article_content or "",
            )
            out[key] = proba
        except Exception:
            out[key] = None

    return out
