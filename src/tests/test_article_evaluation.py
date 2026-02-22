"""Test article evaluation via factuality.run."""

import asyncio
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root)


def test_article():
    from src import run

    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        print("Skip: GOOGLE_API_KEY or GEMINI_API_KEY not set")
        return

    async def _run():
        return await run(
            article_title="Breaking: Major Policy Change Announced",
            article_content="The administration announced a major policy shift today.",
            article_url="https://example.com/article",
            predictive_scores=None,
        )

    result = asyncio.run(_run())
    assert "factor_scores" in result
    assert "combined_veracity_score" in result
    assert "overall_assessment" in result
    print("Combined score:", result["combined_veracity_score"])
    print("Assessment:", result["overall_assessment"])


if __name__ == "__main__":
    test_article()
