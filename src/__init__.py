"""
Factuality assessment pipeline.

Multi-agent evaluation of news articles on six factors (political affiliation,
clickbait, sensationalism, title-body alignment, sentiment, toxicity) using
Google ADK and Gemini. Optional predictive model scores can be injected into
the prompt.
"""

from src.app import FACTUALITY_FACTORS, SCORING_RECIPES, app, create_app
from src.models import get_predictive_scores
from src.run import build_prompt, run

try:
    from importlib.metadata import version
    __version__ = version("capstone-a1")
except Exception:
    __version__ = "0.1.0"

__all__ = [
    "app",
    "create_app",
    "run",
    "build_prompt",
    "get_predictive_scores",
    "FACTUALITY_FACTORS",
    "SCORING_RECIPES",
    "__version__",
]
