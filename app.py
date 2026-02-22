"""Streamlit UI. Run with: streamlit run app.py"""

import asyncio
import concurrent.futures
import sys
from pathlib import Path

import streamlit as st

_project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_project_root))
try:
    from dotenv import load_dotenv
    load_dotenv(_project_root / ".env")
except ImportError:
    pass
from src import run, get_predictive_scores
from src.app import PATTERNS, create_app

PATTERN_LABELS = {
    "simple_prompt": "Simple prompt",
    "function_calling": "Function calling",
    "simple_plus_function": "Simple + function",
    "basic_cot": "Basic chain-of-thought",
    "cot": "Full CoT",
    "fcot": "Full FCoT",
    "complex_prompt": "Complex prompt",
}

# Add your report and repo URLs here for the Overview tab (use "" to hide a link)
REPORT_URL = ""
GITHUB_URL = ""

st.set_page_config(page_title="Factuality Evaluator", layout="wide")

tab_overview, tab_evaluate = st.tabs(["Overview", "Evaluate"])

# -----------------------------------------------------------------------------
# Overview tab: public-facing project summary (general audience)
# -----------------------------------------------------------------------------
with tab_overview:
    st.title("Factuality Evaluator for News Articles")
    st.markdown("*Helping readers and fact-checkers assess how reliable a news article is.*")

    st.header("Why this matters")
    st.markdown("""
    Misinformation and biased reporting make it hard to trust what we read. We built a tool that scores news articles on **six factuality dimensions**—from political bias and clickbait to toxicity and headline–body alignment—and combines them into a single reliability score. The goal is to give a quick, interpretable signal of how trustworthy an article is, and to encourage people to look closer when something looks off.
    """)

    st.header("What we built")
    st.markdown("""
    Our system uses **multiple AI agents** working together: one agent per dimension (e.g., “How clickbait is the headline?” or “How balanced is the political framing?”), then a final agent that weighs their answers and produces a **combined veracity score** (0–10, lower = more reliable) plus a short written assessment. You can try it yourself in the **Evaluate** tab by pasting an article title and content.
    """)

    st.header("How we approached it")
    st.markdown("""
    We experimented with different ways to prompt the AI—from very simple instructions to structured “chain-of-thought” (step-by-step reasoning) and a “fractal” version with verification and self-correction. We also gave some agents access to **web search** so they can check claims against external sources. The pipeline is built with the Google Agent Development Kit (ADK) and Gemini.
    """)
    with st.expander("More on our prompting strategies"):
        st.markdown("""
        - **Simple prompt** — Direct scoring with a short recipe; no extra steps.
        - **Function calling** — Same as simple, but the model can use Google Search to verify facts.
        - **Basic chain-of-thought** — Generic “identify evidence → evaluate → synthesize” steps.
        - **Full CoT** — Factor-specific reasoning steps plus search; tailored instructions per dimension.
        - **Full FCoT** — A four-step “fractal” flow (problem → solution → verification → justification) with optional sub-questions and re-grounding when search contradicts the draft.
        - **Complex prompt** — Expert fact-checker role and a detailed paragraph, no fixed steps.

        We found that **no single strategy wins on every dimension**. Simpler prompts did best on concrete factors like toxicity; search helped most on title–body alignment; and structured reasoning (Full CoT) led on nuanced factors like political bias and sensationalism.
        """)

    st.header("Results and impact")
    st.markdown("""
    We evaluated our prompting strategies on human-labeled articles. The main takeaway: **the best strategy depends on what you’re measuring**. For example, a minimal “simple” prompt agreed with humans most on toxicity, while adding web search gave the best agreement on whether the headline matches the body. Our more structured strategies (Full CoT and Full FCoT) did best on political affiliation and sensationalism and give interpretable step-by-step explanations—so we use them as the default in the app, while keeping the others available for comparison.
    """)
    st.info("Want the full numbers? Check out our **report** and **code** (links below) for tables, methodology, and to run your own evaluations.")

    st.header("Try it and learn more")
    st.markdown("Use the **Evaluate** tab to score any article. For the full write-up, methodology, and results tables, see:")
    st.markdown(f"- **Full report** — [Read the report]({REPORT_URL})" if REPORT_URL else "- **Full report**")
    st.markdown(f"- **GitHub** — [View code and data]({GITHUB_URL})" if GITHUB_URL else "- **GitHub**")
    st.caption("Built with Google ADK and Gemini. Data and licenses: see the repository.")

# -----------------------------------------------------------------------------
# Evaluate tab: existing evaluator UI
# -----------------------------------------------------------------------------
with tab_evaluate:
    st.title("Factuality Evaluator")
    st.markdown("Six factors → combiner → combined prediction (ADK pipeline).")

    evaluation_style = st.selectbox(
        "Evaluation style",
        options=PATTERNS,
        format_func=lambda p: PATTERN_LABELS.get(p, p),
        index=PATTERNS.index("cot") if "cot" in PATTERNS else 0,
    )
    article_title = st.text_input("Article Title", placeholder="Enter title...")
    article_content = st.text_area("Article Content", height=300, placeholder="Paste article text...")
    article_url = st.text_input("Article URL (optional)", placeholder="https://...")

    if st.button("Evaluate", type="primary") and article_title and article_content:
        with st.spinner("Running pipeline..."):
            predictive_scores = get_predictive_scores(
                article_title, article_content, article_url or ""
            )
            try:
                app_instance = create_app(pattern=evaluation_style)
                try:
                    result = asyncio.run(
                        run(
                            article_title=article_title,
                            article_content=article_content,
                            article_url=article_url or "",
                            predictive_scores=predictive_scores or None,
                            app_instance=app_instance,
                        )
                    )
                except RuntimeError:
                    def _run_async():
                        return asyncio.run(
                            run(
                                article_title=article_title,
                                article_content=article_content,
                                article_url=article_url or "",
                                predictive_scores=predictive_scores or None,
                                app_instance=app_instance,
                            )
                        )
                    with concurrent.futures.ThreadPoolExecutor() as ex:
                        result = ex.submit(_run_async).result()
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                result = None
        if result is None:
            st.warning("Evaluation did not complete. Check that GOOGLE_API_KEY or GEMINI_API_KEY is set in .env.")
        else:
            combined = result.get("combined_veracity_score")
            st.subheader("Combined veracity score")
            st.metric("Score (0–10, lower = more reliable)", combined if combined is not None else "N/A")
            st.subheader("Overall assessment")
            st.write(result.get("overall_assessment") or "No assessment returned.")
            st.subheader("Factor scores")
            st.json(result.get("factor_scores", {}))
            with st.expander("Explanations"):
                st.json(result.get("explanations", {}))
