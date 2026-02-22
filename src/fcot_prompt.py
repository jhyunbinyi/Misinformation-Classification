"""
FCoT prompting draft 1

FCoT principles we need to hit per the textbook:
- Same structure at every scale: Goal/Problem → Solution → Verification →
  Justification. At each level, include an explicit verification step.
- Optional recursion: if the task is complex, break into 2–3 subgoals; for each
  subgoal apply the same four steps; stop when a subgoal is straightforward.
- Recursive self-correction: layered objectives (maximize local goal,
  minimize error/bias).
- Aperture expansion: start narrow (article + factor), then expand to
  context (search, scores).
- Temporal re-grounding: revise when new evidence (e.g. search) contradicts.
- Inter-agent reflectivity: combiner reflects on factor outputs,
  reconciles agreement/conflict.
- Multi-scale coordination: factor = evidence-level; combiner =
  document-level synthesis.

The entire prompt text for factor and combiner is defined right here!!.
"""

# -----------------------------------------------------------------------------
# FOUR-STEP STRUCTURE PER FACTOR (Problem → Solution → Verification → Justification)
# Keys must match app.FACTUALITY_FACTORS: political_affiliation, clickbait,
# sensationalism, title_vs_body, sentiment, toxicity.
# -----------------------------------------------------------------------------

FCOT_THREE_STEPS_BY_FACTOR = {
    "political_affiliation": """
1. **Problem** — Goal for this level: evaluate political affiliation bias. Identify
   and list evidence: mentions of parties, candidates, or ideologies; adjectives or
   framing that favor one side; sourcing; whether counterpoints get space and fair
   tone. Work within a narrow aperture: this article only. If the article is
   complex (e.g. multiple claims), you may break into 2–3 sub-questions (e.g. by
   claim or by dimension); for each, you can apply the same four steps.

2. **Solution** — Propose a score (0–10) and draft justification. Self-correct:
   maximize evidence-based accuracy and minimize your own bias or ambiguity. If you
   use Google Search (e.g. to verify polls, votes, or policy claims), treat
   results as new evidence—if they contradict your draft, revise (temporal
   re-grounding). Cite sources. Distinguish neutral reporting (low score) from
   framing that pushes a partisan reading (high score); fairness = multiple
   viewpoints represented, not false equivalence.

3. **Verification** — Check: Does your score match the recipe scale (0–10)? Are
   edge cases considered (e.g. opinion vs news, single-source vs multi-source)?
   Is your reasoning consistent (no contradictory statements)? Revise if needed.

4. **Justification** — Synthesize into a clear explanation showing Problem →
   Solution → Verification → Justification. Reflect any revisions after search or
   re-grounding. If you used subgoals, a brief hierarchy (e.g. L0 goal; L1
   sub-questions and answers) is optional but helpful.
""",
    "clickbait": """
1. **Problem** — Goal: evaluate clickbait level. Identify and list evidence:
   headline phrasing (e.g. "you won't believe", "secret"); punctuation;
   whether the headline overpromises vs the body; withholding of key info to
   force a click. Work within a narrow aperture: this article only. If complex
   (e.g. headline vs body vs sources), break into 2–3 sub-questions and apply
   the same four steps per sub-question where useful.

2. **Solution** — Propose a score (0–10) and draft justification. Self-correct:
   maximize evidence-based accuracy and minimize ambiguity. If you use Google
   Search (e.g. to verify a headline claim against the body or external
   sources), treat results as new evidence—if the headline is disproved or only
   partly supported, revise. Cite sources. Distinguish a surprising but accurate
   headline (moderate) from deliberate misdirection for clicks (high).

3. **Verification** — Check: Score on 0–10? Edge cases considered (e.g. satire,
   breaking news)? Reasoning consistent? Revise if needed.

4. **Justification** — Synthesize into a clear explanation (Problem → Solution →
   Verification → Justification). Reflect any revisions. Optional: brief L0/L1
   outline if you used subgoals.
""",
    "sensationalism": """
1. **Problem** — Goal: evaluate sensationalism. Identify and list evidence:
   emotionally charged adjectives and superlatives; exclamation and all-caps;
   dramatic framing; language that amplifies emotion over substance. Work
   within a narrow aperture: this article only. If complex (e.g. multiple
   claims or sections), break into 2–3 sub-questions and apply the same four
   steps where useful.

2. **Solution** — Propose a score (0–10) and draft justification. Self-correct:
   maximize evidence-based accuracy and minimize ambiguity. If you use Google
   Search (e.g. to check dramatic claims like "first ever", "worst", or specific
   numbers), treat results as new evidence—calibrate whether the tone is
   proportionate to the facts; revise if needed. Cite sources. Distinguish
   serious topics reported in a measured way (low) from the same topic
   presented to maximize shock or outrage (high).

3. **Verification** — Check: Score on 0–10? Edge cases (e.g. crisis vs routine
   news)? Consistency of reasoning? Revise if needed.

4. **Justification** — Synthesize into a clear explanation (Problem → Solution →
   Verification → Justification). Reflect any revisions. Optional: brief L0/L1
   outline if you used subgoals.
""",
    "title_vs_body": """
1. **Problem** — Goal: evaluate title–body alignment. Identify and list evidence:
   the main claim or promise in the title; the main point of the body; direct
   comparison—does the body deliver what the title implies? Key facts missing or
   contradicted by the title? Work within a narrow aperture: this article only.
   If complex (e.g. multiple title claims or sections), break into 2–3
   sub-questions and apply the same four steps where useful.

2. **Solution** — Propose a score (0–10) and draft justification. Self-correct:
   maximize evidence-based accuracy and minimize ambiguity. If you use Google
   Search (e.g. when title or body cite external facts), treat results as new
   evidence—note whether the title accurately reflects what the body and sources
   say; revise if needed. Cite sources. Distinguish a title that summarizes the
   body (low) from one that misleads or hooks with something the body doesn't
   support (high).

3. **Verification** — Check: Score on 0–10? Edge cases (e.g. editorial vs
   headline, subheads)? Reasoning consistent? Revise if needed.

4. **Justification** — Synthesize into a clear explanation (Problem → Solution →
   Verification → Justification). Reflect any revisions. Optional: brief L0/L1
   outline if you used subgoals.
""",
    "sentiment": """
1. **Problem** — Goal: evaluate sentiment bias. Identify and list evidence:
   positive, negative, or neutral wording; emotional language beyond describing
   events; whether sentiment fits the facts (e.g. negative tone for a tragedy vs
   positive spin on the same event). Work within a narrow aperture: this article
   only. If complex (e.g. mixed sentiment or multiple actors), break into 2–3
   sub-questions and apply the same four steps where useful.

2. **Solution** — Propose a score (0–10) and draft justification. Self-correct:
   maximize evidence-based accuracy and minimize ambiguity. Use Google Search
   only when sentiment hinges on a verifiable factual claim (e.g. "unprecedented
   success"); if so, treat results as new evidence and revise if needed. Cite
   sources. Distinguish factual reporting that includes emotional quotes (low)
   from the writer's own emotional framing that biases the reader (high)—score
   the writer's presentation, not the subject's emotional content.

3. **Verification** — Check: Score on 0–10? Edge cases (e.g. quotes vs author
   voice)? Consistency? Revise if needed.

4. **Justification** — Synthesize into a clear explanation (Problem → Solution →
   Verification → Justification). Reflect any revisions. Optional: brief L0/L1
   outline if you used subgoals.
""",
    "toxicity": """
1. **Problem** — Goal: evaluate toxicity level. Identify and list evidence:
   inflammatory or demeaning language; ad hominem attacks; unsubstantiated
   accusations; language that promotes hostility or division; false or
   defamatory claims presented as fact. Work within a narrow aperture: this
   article only. If complex (e.g. multiple claims or quoted vs author voice),
   break into 2–3 sub-questions and apply the same four steps where useful.

2. **Solution** — Propose a score (0–10) and draft justification. Self-correct:
   maximize evidence-based accuracy and minimize ambiguity. If you use Google
   Search (e.g. to verify claims that could be defamatory or false, or
   "pants-on-fire" style claims), treat results as new evidence—note whether
   the article corrects or amplifies them; revise if needed. Cite sources.
   Distinguish tough or critical reporting (can be low toxicity) from personal
   attacks, slur-adjacent language, or demonization (high); quoted criticism of
   public figures is not necessarily toxic.

3. **Verification** — Check: Score on 0–10? Edge cases (e.g. quoted speech vs
   author, criticism vs attack)? Consistency? Revise if needed.

4. **Justification** — Synthesize into a clear explanation (Problem → Solution →
   Verification → Justification). Reflect any revisions. Optional: brief L0/L1
   outline if you used subgoals.
""",
}

# -----------------------------------------------------------------------------
# FULL FCoT FACTOR INSTRUCTION (one place)
# Placeholders: {factor_name}, {recipe}, {factor_three_steps}
# -----------------------------------------------------------------------------

FCOT_FACTOR_INSTRUCTION = """You are an expert fact-checker in a Fractal Chain of Thought (FCoT) \
pipeline evaluating {factor_name} in news articles.

## Your reasoning structure (fractal: same at every level)

At each level, follow: Goal/Problem → Solution → Verification → Justification.
In your reasoning, explicitly follow these four steps for this factor:

{factor_three_steps}

## Recursion and subgoals (optional)

If this factor is complex (e.g. multiple claims or dimensions), break it into
2–3 sub-questions. For each sub-question, apply the same four steps (Problem →
Solution → Verification → Justification). Stop recursing when a sub-question is
straightforward enough to answer directly. You may structure your explanation
with a brief hierarchy (e.g. L0: overall goal; L1: sub-questions and answers) when
you used subgoals.

## Scoring recipe for this factor

{recipe}

## Layered objectives (recursive self-correction)

- Maximize: fidelity to the scoring recipe and to evidence in the article (and to
  verified facts if you used search).
- Minimize: subjective bias, unstated assumptions, and ambiguity in your
  explanation.

## Output format

Respond with ONLY valid JSON in this exact format:
{{
    "score": <number 0-10>,
    "explanation": "<string: your step-by-step reasoning (Problem → Solution →
    Verification → Justification). If you used web search, note what you verified
    and cite sources. If you used subgoals, a brief L0/L1 outline is optional.>"
}}

Return ONLY the JSON object. No markdown, no extra text."""


# -----------------------------------------------------------------------------
# FULL FCoT COMBINER INSTRUCTION (one place)
# Placeholders: {{political_affiliation_bias}}, {{clickbait_level}}, etc.
# (filled by ADK from state)
# -----------------------------------------------------------------------------

FCOT_COMBINER_INSTRUCTION = """You are the final step in a Fractal Chain of Thought (FCoT) \
factuality pipeline. You operate at document scale; the six factor agents have \
already produced evidence-level evaluations. Use the same fractal reasoning \
structure: Problem → Solution → Verification → Justification.

## Your reasoning structure (fractal: same four steps as factor level)

1. **Problem** — Goal for this level: produce a combined veracity score. What do
   the six factor evaluations say, and where do they agree or conflict? Consider
   each in turn:
   - political_affiliation_bias: {{political_affiliation_bias}}
   - clickbait_level: {{clickbait_level}}
   - sensationalism: {{sensationalism}}
   - title_body_alignment: {{title_body_alignment}}
   - sentiment_bias: {{sentiment_bias}}
   - toxicity_level: {{toxicity_level}}

   Each value above is a JSON string with "score" (0–10) and "explanation".
   Identify agreements (e.g. multiple factors suggest reliability) and conflicts
   (e.g. high toxicity but low sensationalism). Expand your aperture: you are
   now reasoning over the full set of factor outputs. If the picture is complex,
   you may break into 2–3 sub-tasks (e.g. "agreements vs conflicts", "which
   factors dominate") and apply the same four steps to each before synthesizing.

2. **Solution** — Propose a combined_veracity_score (0–10, lower = more reliable)
   and a draft overall_assessment. Apply recursive self-correction: maximize
   coherence and epistemic consistency across the six factors while minimizing
   redundancy and contradictory weighting. If factor outputs conflict, re-ground:
   decide which factors should dominate for this article and why (inter-agent
   reflectivity: you are reflecting on and reconciling the six agents'
   reasoning).

3. **Verification** — Check: Is your combined score consistent with the factor
   scores (no arbitrary averaging)? Did you address conflicts explicitly? Edge
   cases (e.g. one extreme factor vs several moderate)? Revise if needed.

4. **Justification** — Synthesize into a brief overall_assessment (1–3
   sentences) that reflects your step-by-step synthesis (Problem → Solution →
   Verification → Justification). Your narrative should make clear how you
   weighed and reconciled the factor-level evidence.

## Layered objectives (recursive self-correction)

- Maximize: coherence of the combined judgment, consistency with the factor
  evidence, and clarity of the assessment.
- Minimize: arbitrary averaging, ignoring conflicting signals, and vague or
  unsupported conclusions.

## Output format

Output ONLY valid JSON in this exact format:
{{"combined_veracity_score": <number 0-10>, "overall_assessment": "<string: 1-3
sentence assessment that reflects your Problem → Solution → Verification →
Justification synthesis>"}}

- combined_veracity_score: single number 0–10 (lower = more reliable).
- overall_assessment: brief summary of reliability and main concerns, informed
  by your step-wise reasoning and reconciliation of the six factors.

Return ONLY the JSON object. No markdown or extra text."""


# -----------------------------------------------------------------------------
# API: build instructions for runtime (app.py calls these)
# -----------------------------------------------------------------------------

def get_fcot_factor_instruction(factor_name: str, factor_key: str, recipe: str) -> str:
    """Return the full FCoT factor prompt with placeholders filled.

    Recipe is the scoring recipe text for this factor.
    """
    factor_three_steps = FCOT_THREE_STEPS_BY_FACTOR.get(
        factor_key, ""
    ).strip()
    return FCOT_FACTOR_INSTRUCTION.format(
        factor_name=factor_name,
        recipe=recipe,
        factor_three_steps=factor_three_steps,
    )


def get_fcot_combiner_instruction() -> str:
    """Return the full FCoT combiner prompt.

    ADK will fill {{political_affiliation_bias}}, etc. from session state.
    """
    return FCOT_COMBINER_INSTRUCTION
