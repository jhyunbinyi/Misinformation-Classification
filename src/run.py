"""
Run the pipeline: session → Runner → run → return state.
"""

import json
import re
import uuid
from typing import Any, Dict, Optional

from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from src.app import FACTUALITY_FACTORS, app


def build_prompt(
    article_title: str,
    article_content: str,
    article_url: str = "",
    predictive_scores: Optional[Dict[str, Any]] = None,
) -> str:
    scores_block = ""
    if predictive_scores:
        pa = predictive_scores.get("pa_proba")
        cb = predictive_scores.get("cb_proba")
        s = predictive_scores.get("s_proba")
        sa = predictive_scores.get("sa_proba")
        t = predictive_scores.get("t_proba")
        tvb = predictive_scores.get("tvb_proba")

        def fmt(p, labels):
            if p is None:
                return "N/A"
            if isinstance(p, list):
                return ", ".join(f"{labels[i]}: {x:.3f}" for i, x in enumerate(p))
            return str(p)

        scores_block = """
PREDICTIVE MODEL PROBABILITY VECTORS (for reference only):
- Political Affiliation: {}
- Clickbait: {}
- Sensationalism: {}
- Title-Body: {}
- Sentiment: {}
- Toxicity: {}
""".format(
            fmt(pa, ["Democrat", "Republican"]),
            fmt(cb, ["Not Clickbait", "Clickbait"]),
            fmt(s, ["Not Sensational", "Sensational"]),
            fmt(tvb, ["Aligned", "Misaligned"]),
            fmt(sa, ["Negative", "Neutral", "Positive"]),
            fmt(t, ["Non-toxic", "Toxic"]),
        )

    return f"""ARTICLE TO ANALYZE:
Title: {article_title}
URL: {article_url or "Not provided"}
Content: {article_content}
{scores_block}

Analyze this article according to your factuality factor and provide your evaluation."""


def _sanitize_json_string(s: str) -> str:
    """Replace unescaped control characters (e.g. raw newlines in strings) so json.loads does not fail."""
    return "".join(c if ord(c) >= 32 else " " for c in s)


def _parse_json(text: str) -> Dict[str, Any]:
    """Parse JSON from agent output. On failure, try to extract score/explanation or combined fields."""
    t = text.strip()
    if "```json" in t:
        start = t.find("```json") + 7
        end = t.find("```", start)
        end = len(t) if end == -1 else end
        t = t[start:end].strip()
    elif "```" in t:
        start = t.find("```") + 3
        end = t.find("```", start)
        end = len(t) if end == -1 else end
        t = t[start:end].strip()
    if not t.startswith("{"):
        i, j = t.find("{"), t.rfind("}")
        if i != -1 and j != -1 and j > i:
            t = t[i : j + 1]
    t = _sanitize_json_string(t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    # Repair attempt: newlines inside string values often break JSON; replace \r\n and \n with space
    # (only when they appear between quotes that look like a value, not after \)
    t_repaired = re.sub(r'(?<!\\)\n|\r\n?', " ", t)
    try:
        return json.loads(t_repaired)
    except json.JSONDecodeError:
        pass
    # Fallback: try to extract factor-style {"score": N, "explanation": "..."}
    m = re.search(r'"score"\s*:\s*(\d+(?:\.\d*)?)', t)
    if m:
        score = int(float(m.group(1)))
        ex_m = re.search(r'"explanation"\s*:\s*"(.*?)"\s*[,}]', t, re.DOTALL)
        explanation = (ex_m.group(1).replace("\\n", "\n").replace('\\"', '"') if ex_m else "")
        return {"score": score, "explanation": explanation}
    # Fallback: try combiner-style {"combined_veracity_score": N, "overall_assessment": "..."}
    m = re.search(r'"combined_veracity_score"\s*:\s*(\d+(?:\.\d*)?)', t)
    if m:
        score = int(float(m.group(1)))
        ex_m = re.search(r'"overall_assessment"\s*:\s*"(.*?)"\s*[,}]', t, re.DOTALL)
        overall = (ex_m.group(1).replace("\\n", "\n").replace('\\"', '"') if ex_m else "")
        return {"combined_veracity_score": score, "overall_assessment": overall}
    return {}


async def run(
    article_title: str,
    article_content: str,
    article_url: str = "",
    predictive_scores: Optional[Dict[str, Any]] = None,
    app_instance: Optional[App] = None,
) -> Dict[str, Any]:
    """
    Run the factuality pipeline. Returns factor_scores, explanations, combined_veracity_score, overall_assessment.
    """
    app_to_use = app_instance or app
    session_service = InMemorySessionService()
    runner = Runner(app=app_to_use, session_service=session_service)
    app_name = app_to_use.name
    user_id = "eval_user"
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    prompt = build_prompt(
        article_title=article_title,
        article_content=article_content,
        article_url=article_url,
        predictive_scores=predictive_scores,
    )
    user_message = Content(parts=[Part(text=prompt)])

    async for _ in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        pass

    session = await session_service.get_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    state = session.state or {}

    factor_scores = {}
    explanations = {}
    for _name, _key, output_key in FACTUALITY_FACTORS:
        raw = state.get(output_key)
        if isinstance(raw, str) and raw.strip():
            parsed = _parse_json(raw)
            factor_scores[output_key] = parsed.get("score")
            explanations[output_key] = parsed.get("explanation", "")
        else:
            factor_scores[output_key] = None
            explanations[output_key] = ""

    combined_raw = state.get("combined_prediction")
    combined_veracity_score = None
    overall_assessment = ""
    if isinstance(combined_raw, str) and combined_raw.strip():
        parsed = _parse_json(combined_raw)
        combined_veracity_score = parsed.get("combined_veracity_score")
        overall_assessment = parsed.get("overall_assessment", "")

    return {
        "factor_scores": factor_scores,
        "explanations": explanations,
        "combined_veracity_score": combined_veracity_score,
        "overall_assessment": overall_assessment,
    }
