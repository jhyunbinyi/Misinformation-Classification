"""Example: run the factuality pipeline."""

import asyncio
from pathlib import Path

# Project root
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import run, get_predictive_scores


async def main():
    article_title = "Breaking: Major Policy Change Announced"
    article_content = """
    In a surprising turn of events, the administration announced a major policy shift
    today. The new policy will affect millions of citizens across the country.
    Critics argue that the change is politically motivated, while supporters claim
    it addresses long-standing issues.
    """
    article_url = "https://example.com/article"
    predictive_scores = get_predictive_scores(article_title, article_content, article_url)

    result = await run(
        article_title=article_title,
        article_content=article_content,
        article_url=article_url,
        predictive_scores=predictive_scores or None,
    )
    print("Factor scores:", result["factor_scores"])
    print("Combined veracity score:", result["combined_veracity_score"])
    print("Overall assessment:", result["overall_assessment"])


if __name__ == "__main__":
    asyncio.run(main())
