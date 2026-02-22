"""Streamlit UI. Run with: streamlit run app.py"""

import asyncio
import concurrent.futures
import os
import sys
from pathlib import Path

import streamlit as st

_project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_project_root))
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

st.set_page_config(page_title="Factuality Evaluator", layout="wide")

# Evaluator UI only (overview lives on GitHub Pages)
st.title("Factuality Evaluator")
st.markdown("Six factors → combiner → combined prediction (ADK pipeline).")

api_key = st.text_input(
    "Gemini API key",
    type="password",
    placeholder="Paste your Google AI / Gemini API key here",
    help="Get a key at [Google AI Studio](https://aistudio.google.com/app/apikey). Your key is not stored.",
)
if not (api_key or "").strip():
    st.caption("Enter your API key above to run evaluations. It is only used for this session and not saved.")

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
    if not api_key or not api_key.strip():
        st.error("Please enter your Gemini API key above to run the evaluation.")
    else:
        os.environ["GOOGLE_API_KEY"] = api_key.strip()
        os.environ["GEMINI_API_KEY"] = api_key.strip()
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
                st.warning("Evaluation did not complete. Check that your API key is valid and has Gemini API access.")
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
