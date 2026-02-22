"""
Single source of truth for Chain of Thought (CoT) prompting.

CoT structure: explicit step-by-step reasoning before the answer.
- Identify: gather evidence from the article relevant to this factor.
- Evaluate: assess that evidence against the scoring criteria.
- Synthesize: combine into a single score (0–10) and explanation.

Optional: agents can use Google Search to verify claims; if so, treat
results as evidence and cite sources.

The entire prompt text for factor and combiner is defined below in one place.
"""

# -----------------------------------------------------------------------------
# THREE-STEP STRUCTURE PER FACTOR (Identify → Evaluate → Synthesize)
# Keys must match app.FACTUALITY_FACTORS: political_affiliation, clickbait,
# sensationalism, title_vs_body, sentiment, toxicity.
# -----------------------------------------------------------------------------

COT_THREE_STEPS_BY_FACTOR = {
    "political_affiliation": """
1. **Identify** — List concrete evidence in the article: mentions of parties,
   candidates, or ideologies; adjectives or framing that favor one side;
   sourcing that leans one way; whether counterpoints get space and fair tone.

2. **Evaluate** — For each piece of evidence, assess it against the scoring
   recipe. Note how it supports or contradicts the criteria. If you use Google
   Search to verify polls, votes, or policy claims, treat results as evidence
   and cite sources. Distinguish neutral reporting (low score) from framing
   that pushes a partisan reading (high score).

3. **Synthesize** — Combine your evaluations into a single score (0–10) and a
   clear explanation that reflects this step-by-step reasoning.
""",
    "clickbait": """
1. **Identify** — List concrete evidence: headline phrasing (e.g. "you won't
   believe", "secret"); punctuation (exclamation/question marks); whether
   the headline overpromises vs the body; withholding of key info to force a
   click.

2. **Evaluate** — For each piece of evidence, assess it against the scoring
   recipe. If you use Google Search to verify a headline claim against the
   body or external sources, treat results as evidence and cite sources.
   Distinguish a surprising but accurate headline (moderate) from deliberate
   misdirection for clicks (high).

3. **Synthesize** — Combine your evaluations into a single score (0–10) and a
   clear explanation that reflects this step-by-step reasoning.
""",
    "sensationalism": """
1. **Identify** — List concrete evidence: emotionally charged adjectives and
   superlatives; exclamation and all-caps; dramatic framing of facts;
   language that amplifies emotion over substance.

2. **Evaluate** — For each piece of evidence, assess it against the scoring
   recipe. If you use Google Search to check dramatic claims (e.g. "first
   ever", "worst", or specific numbers), treat results as evidence and
   cite sources. Distinguish serious topics reported in a measured way (low)
   from the same topic presented to maximize shock or outrage (high).

3. **Synthesize** — Combine your evaluations into a single score (0–10) and a
   clear explanation that reflects this step-by-step reasoning.
""",
    "title_vs_body": """
1. **Identify** — List concrete evidence: the main claim or promise in the
   title; the main point of the body; direct comparison—does the body deliver
   what the title implies? Are key facts from the body missing from or
   contradicted by the title?

2. **Evaluate** — For each piece of evidence, assess it against the scoring
   recipe. If you use Google Search when title or body cite external facts,
   treat results as evidence and cite sources. Distinguish a title that
   summarizes the body (low) from one that misleads or hooks with something
   the body doesn't support (high).

3. **Synthesize** — Combine your evaluations into a single score (0–10) and a
   clear explanation that reflects this step-by-step reasoning.
""",
    "sentiment": """
1. **Identify** — List concrete evidence: positive, negative, or neutral
   wording; emotional language beyond describing events; whether sentiment
   fits the facts (e.g. negative tone for a tragedy vs positive spin on the
   same event).

2. **Evaluate** — For each piece of evidence, assess it against the scoring
   recipe. Use Google Search only when sentiment hinges on a verifiable
   factual claim (e.g. "unprecedented success"); if so, cite sources.
   Distinguish factual reporting that includes emotional quotes (low) from
   the writer's own emotional framing that biases the reader (high)—score
   the writer's presentation, not the subject's emotional content.

3. **Synthesize** — Combine your evaluations into a single score (0–10) and a
   clear explanation that reflects this step-by-step reasoning.
""",
    "toxicity": """
1. **Identify** — List concrete evidence: inflammatory or demeaning language;
   ad hominem attacks; unsubstantiated accusations; language that promotes
   hostility or division; false or defamatory claims presented as fact.

2. **Evaluate** — For each piece of evidence, assess it against the scoring
   recipe. If you use Google Search to verify claims that could be
   defamatory or false, or "pants-on-fire" style claims, treat results as
   evidence and cite sources. Distinguish tough or critical reporting (can
   be low toxicity) from personal attacks, slur-adjacent language, or
   demonization (high); quoted criticism of public figures is not
   necessarily toxic.

3. **Synthesize** — Combine your evaluations into a single score (0–10) and a
   clear explanation that reflects this step-by-step reasoning.
""",
}

# -----------------------------------------------------------------------------
# FULL CoT FACTOR INSTRUCTION (one place)
# Placeholders: {factor_name}, {recipe}, {factor_three_steps}
# -----------------------------------------------------------------------------

COT_FACTOR_INSTRUCTION = """You are an expert fact-checker evaluating {factor_name} \
in news articles. Use chain-of-thought reasoning before giving your final score.

## Your reasoning structure (Identify → Evaluate → Synthesize)

In your reasoning, explicitly follow these three steps for this factor:

{factor_three_steps}

## Scoring recipe for this factor

{recipe}

## Output format

Respond with ONLY valid JSON in this exact format:
{{
    "score": <number 0-10>,
    "explanation": "<string: your step-by-step reasoning (Identify → Evaluate →
    Synthesize). If you used web search, note what you verified and cite
    sources.>"
}}

Return ONLY the JSON object. No markdown, no extra text."""


# -----------------------------------------------------------------------------
# FULL CoT COMBINER INSTRUCTION (one place)
# Placeholders: {{political_affiliation_bias}}, {{clickbait_level}}, etc.
# (filled by ADK from state)
# -----------------------------------------------------------------------------

COT_COMBINER_INSTRUCTION = """You are the final step in a factuality pipeline. \
The six factor agents have produced evidence-level evaluations. Use \
chain-of-thought before giving your combined prediction.

## Your reasoning structure (Identify → Evaluate → Synthesize)

1. **Identify** — Consider each factor output in turn:
   - political_affiliation_bias: {{political_affiliation_bias}}
   - clickbait_level: {{clickbait_level}}
   - sensationalism: {{sensationalism}}
   - title_body_alignment: {{title_body_alignment}}
   - sentiment_bias: {{sentiment_bias}}
   - toxicity_level: {{toxicity_level}}

   Each value above is a JSON string with "score" (0–10) and "explanation".
   Note the score and key points from each explanation.

2. **Evaluate** — Weigh agreements and conflicts. Where do factors agree (e.g.
   multiple suggest reliability)? Where do they conflict (e.g. high toxicity
   but low sensationalism)? Decide which factors should influence the overall
   veracity most for this article.

3. **Synthesize** — Combine your reasoning into a single combined_veracity_score
   (0–10, lower = more reliable) and a brief overall_assessment (1–3
   sentences) that reflects this step-by-step synthesis.

## Output format

Output ONLY valid JSON in this exact format:
{{"combined_veracity_score": <number 0-10>, "overall_assessment": "<string: 1-3
sentence assessment that reflects your Identify → Evaluate → Synthesize
synthesis>"}}

- combined_veracity_score: single number 0–10 (lower = more reliable).
- overall_assessment: brief summary of reliability and main concerns.

Return ONLY the JSON object. No markdown or extra text."""


# -----------------------------------------------------------------------------
# API: build instructions for runtime (app.py calls these)
# -----------------------------------------------------------------------------

def get_cot_factor_instruction(factor_name: str, factor_key: str, recipe: str) -> str:
    """Return the full CoT factor prompt with placeholders filled.

    Recipe is the scoring recipe text for this factor.
    """
    factor_three_steps = COT_THREE_STEPS_BY_FACTOR.get(
        factor_key, ""
    ).strip()
    return COT_FACTOR_INSTRUCTION.format(
        factor_name=factor_name,
        recipe=recipe,
        factor_three_steps=factor_three_steps,
    )


def get_cot_combiner_instruction() -> str:
    """Return the full CoT combiner prompt.

    ADK will fill {{political_affiliation_bias}}, etc. from session state.
    """
    return COT_COMBINER_INSTRUCTION
