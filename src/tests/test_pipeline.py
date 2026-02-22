"""Tests for the factuality pipeline."""

import asyncio
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root)


def test_app_import():
    from src import app, create_app, FACTUALITY_FACTORS

    assert app is not None
    assert app.name == "factuality_evaluator"
    assert len(FACTUALITY_FACTORS) == 6


def test_run_import():
    from src import run, build_prompt

    assert run is not None
    assert build_prompt is not None


async def test_run_returns_shape():
    from src import run

    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        return

    result = await run(
        article_title="Test title",
        article_content="Short test content.",
        article_url="",
        predictive_scores=None,
    )
    assert "factor_scores" in result
    assert "explanations" in result
    assert "combined_veracity_score" in result
    assert "overall_assessment" in result
    assert len(result["factor_scores"]) == 6


if __name__ == "__main__":
    test_app_import()
    test_run_import()
    asyncio.run(test_run_returns_shape())
    print("All tests passed.")
