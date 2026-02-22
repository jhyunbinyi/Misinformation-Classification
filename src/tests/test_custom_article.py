"""Test evaluation with custom article."""

import asyncio
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root)


def test_custom_article():
    from src import run

    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        print("Skip: GOOGLE_API_KEY or GEMINI_API_KEY not set")
        return

    async def _run():
        return await run(
            article_title="Custom Title",
            article_content="Custom body text for testing.",
            article_url="",
            predictive_scores=None,
        )

    result = asyncio.run(_run())
    assert "factor_scores" in result
    assert "explanations" in result


if __name__ == "__main__":
    test_custom_article()
