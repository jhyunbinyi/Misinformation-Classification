"""
All agents in one place: scoring recipes, factor agents, parallel agent, combiner, pipeline, app.
"""

from google.adk.agents import LlmAgent
from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.apps import App
from google.adk.tools import google_search

from src.cot_prompt import get_cot_combiner_instruction, get_cot_factor_instruction
from src.fcot_prompt import get_fcot_combiner_instruction, get_fcot_factor_instruction

MODEL = "gemini-2.5-flash"

# Keys the combiner expects in session state (must match FACTUALITY_FACTORS output_key).
COMBINER_STATE_KEYS = [
    "political_affiliation_bias",
    "clickbait_level",
    "sensationalism",
    "title_body_alignment",
    "sentiment_bias",
    "toxicity_level",
]


def _combiner_instruction_provider(template: str):
    """Return a callable that fills the combiner template from context.state.

    ADK may not inject parallel-agent state into the combiner's context when
    using pattern-built apps; filling from context.state() avoids
    'Context variable not found' errors.
    """

    def provider(context) -> str:
        state = getattr(context, "state", None)
        if callable(state):
            state = state()
        if not isinstance(state, dict):
            state = dict(state) if state is not None else {}
        data = {k: (state.get(k) or "") for k in COMBINER_STATE_KEYS}
        return template.format(**data)

    return provider

# Tool for fact-checking: agents can query the web when verifying claims.
GOOGLE_SEARCH_TOOL = [google_search]

# -----------------------------------------------------------------------------
# Scoring recipes (used in factor agent instructions)
# -----------------------------------------------------------------------------

SCORING_RECIPES = {
    "political_affiliation": """
    Score Political Affiliation Bias (0-10, where 0=neutral, 10=highly biased):
    1. Identify explicit mentions of political parties, candidates, or ideologies
    2. Assess the tone: neutral reporting (0-3), slight bias (4-6), strong bias (7-10)
    3. Look for loaded language, framing, or selective facts
    4. Consider whether both sides are presented fairly
    """,
    "clickbait": """
    Score Clickbait Level (0-10, where 0=informative, 10=highly clickbait):
    1. Identify sensational language: "shocking", "unbelievable", "you won't believe"
    2. Check for emotional manipulation: excessive exclamation marks, question marks
    3. Assess headline accuracy: does it match the content?
    4. Look for withholding information or creating false urgency
    5. Evaluate if the title is designed to maximize clicks rather than inform
    """,
    "sensationalism": """
    Score Sensationalism (0-10, where 0=factual, 10=highly sensational):
    1. Identify emotionally charged adjectives: "shocking", "horrific", "explosive"
    2. Look for hyperbolic comparisons and superlatives ("best", "worst", "most")
    3. Assess use of exclamation marks and all-caps text
    4. Evaluate if facts are presented in a neutral or emotionally charged manner
    5. Check for dramatic language that overshadows factual content
    """,
    "title_vs_body": """
    Score Title-Body Alignment (0-10, where 0=perfectly aligned, 10=completely misaligned):
    1. Compare the main claim in the title with the body content
    2. Assess if the title accurately represents the article's main point
    3. Look for clickbait tactics: title promises something body doesn't deliver
    4. Evaluate if key information from the body is reflected in the title
    5. Check for misleading framing or selective representation
    """,
    "sentiment": """
    Score Sentiment Bias (0-10, where 0=neutral, 10=highly emotional):
    1. Identify positive, negative, or neutral sentiment in the text
    2. Assess if sentiment is appropriate for factual reporting
    3. Look for emotional language that may bias the reader
    4. Evaluate if the sentiment matches the factual content
    5. Check for manipulation through emotional appeals
    """,
    "toxicity": """
    Score Toxicity Level (0-10, where 0=respectful, 10=highly toxic):
    1. Identify inflammatory, offensive, or harmful language
    2. Assess use of ad hominem attacks or personal insults
    3. Look for false claims labeled as "false" or "pants-on-fire"
    4. Evaluate if the language promotes division or hostility
    5. Check for unsubstantiated accusations or defamatory content
    """,
}

# -----------------------------------------------------------------------------
# Factor list: (display name, key, state output_key)
# -----------------------------------------------------------------------------

FACTUALITY_FACTORS = [
    ("Political Affiliation Bias", "political_affiliation", "political_affiliation_bias"),
    ("Clickbait Level", "clickbait", "clickbait_level"),
    ("Sensationalism", "sensationalism", "sensationalism"),
    ("Title-Body Alignment", "title_vs_body", "title_body_alignment"),
    ("Sentiment Bias", "sentiment", "sentiment_bias"),
    ("Toxicity Level", "toxicity", "toxicity_level"),
]

# -----------------------------------------------------------------------------
# Factor agents (each writes score + explanation to session state)
# -----------------------------------------------------------------------------


def _factor_instruction(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""You are an expert fact-checker evaluating {factor_name} in news articles.

Use chain-of-thought reasoning before giving your final score. In your mind (or in your explanation), follow these steps:
1. Identify: List specific evidence in the article relevant to {factor_name} (quotes, phrases, structural choices).
2. Evaluate: For each piece of evidence, assess it against the scoring recipe below. Note how it supports or contradicts the criteria.
3. Synthesize: Combine your evaluations into a single score (0-10) and a clear explanation that reflects this step-by-step reasoning.

SCORING RECIPE:
{recipe}

You have access to Google Search. When the article makes factual claims (statistics, events, quotes, or verifiable statements), use web search to verify them when it would affect your score or explanation. Cite sources when you use search results.

You will receive article title, content, optional URL, and optional predictive model scores (for reference).

Respond with ONLY valid JSON in this exact format:
{{
    "score": <number 0-10>,
    "explanation": "<string: your step-by-step reasoning (identify → evaluate → synthesize). If you used web search, note what you verified and cite sources.>"
}}

Return ONLY the JSON object, nothing else. No markdown or extra text."""


political_affiliation_agent = LlmAgent(
    name="political_affiliation_evaluator",
    model=MODEL,
    description="Evaluates Political Affiliation Bias. Returns score 0-10 and explanation. Can use Google Search to verify claims.",
    instruction=_factor_instruction("Political Affiliation Bias", "political_affiliation"),
    output_key="political_affiliation_bias",
    tools=GOOGLE_SEARCH_TOOL,
)

clickbait_agent = LlmAgent(
    name="clickbait_evaluator",
    model=MODEL,
    description="Evaluates Clickbait Level. Returns score 0-10 and explanation. Can use Google Search to verify claims.",
    instruction=_factor_instruction("Clickbait Level", "clickbait"),
    output_key="clickbait_level",
    tools=GOOGLE_SEARCH_TOOL,
)

sensationalism_agent = LlmAgent(
    name="sensationalism_evaluator",
    model=MODEL,
    description="Evaluates Sensationalism. Returns score 0-10 and explanation. Can use Google Search to verify claims.",
    instruction=_factor_instruction("Sensationalism", "sensationalism"),
    output_key="sensationalism",
    tools=GOOGLE_SEARCH_TOOL,
)

title_body_agent = LlmAgent(
    name="title_vs_body_evaluator",
    model=MODEL,
    description="Evaluates Title-Body Alignment. Returns score 0-10 and explanation. Can use Google Search to verify claims.",
    instruction=_factor_instruction("Title-Body Alignment", "title_vs_body"),
    output_key="title_body_alignment",
    tools=GOOGLE_SEARCH_TOOL,
)

sentiment_agent = LlmAgent(
    name="sentiment_evaluator",
    model=MODEL,
    description="Evaluates Sentiment Bias. Returns score 0-10 and explanation. Can use Google Search to verify claims.",
    instruction=_factor_instruction("Sentiment Bias", "sentiment"),
    output_key="sentiment_bias",
    tools=GOOGLE_SEARCH_TOOL,
)

toxicity_agent = LlmAgent(
    name="toxicity_evaluator",
    model=MODEL,
    description="Evaluates Toxicity Level. Returns score 0-10 and explanation. Can use Google Search to verify claims.",
    instruction=_factor_instruction("Toxicity Level", "toxicity"),
    output_key="toxicity_level",
    tools=GOOGLE_SEARCH_TOOL,
)

# -----------------------------------------------------------------------------
# Parallel agent (runs all six factor agents)
# -----------------------------------------------------------------------------

parallel_agent = ParallelAgent(
    name="factuality_parallel_evaluator",
    sub_agents=[
        political_affiliation_agent,
        clickbait_agent,
        sensationalism_agent,
        title_body_agent,
        sentiment_agent,
        toxicity_agent,
    ],
    description="Evaluates articles on six factuality factors in parallel.",
)

# -----------------------------------------------------------------------------
# Combiner agent (reads factor outputs from state, writes combined prediction)
# -----------------------------------------------------------------------------

combiner_agent = LlmAgent(
    name="combiner_agent",
    model=MODEL,
    description="Produces combined veracity score and overall assessment from factor evaluations and optional predictive outputs.",
    instruction="""You are the final step in a factuality pipeline. Use chain-of-thought reasoning before giving your combined prediction. Follow these steps in order:

1. Consider each factor in turn: Read political_affiliation_bias, then clickbait_level, then sensationalism, then title_body_alignment, then sentiment_bias, then toxicity_level. For each, note the score and key points from the explanation.
2. Weigh and reconcile: Identify where factors agree or conflict (e.g. high toxicity but low sensationalism). Decide which factors should influence the overall veracity most for this article.
3. Synthesize: Combine your reasoning into a single combined_veracity_score (0-10, lower = more reliable) and a brief overall_assessment that reflects this step-by-step synthesis.

You receive the user message (article and optional predictive model outputs) and the following factor evaluations:

political_affiliation_bias: {political_affiliation_bias}
clickbait_level: {clickbait_level}
sensationalism: {sensationalism}
title_body_alignment: {title_body_alignment}
sentiment_bias: {sentiment_bias}
toxicity_level: {toxicity_level}

Each value above is a JSON string with "score" (0-10) and "explanation".

Output ONLY valid JSON in this exact format:
{"combined_veracity_score": <number 0-10>, "overall_assessment": "<string: 1-3 sentence assessment that reflects your step-wise synthesis of the six factors>"}
- combined_veracity_score: single number 0-10 (lower = more reliable).
- overall_assessment: brief summary of reliability and main concerns, informed by your step-by-step reasoning.

Return ONLY the JSON object. No markdown or extra text.""",
    output_key="combined_prediction",
)

# -----------------------------------------------------------------------------
# Root pipeline: parallel factors → combiner
# -----------------------------------------------------------------------------

root_agent = SequentialAgent(
    name="factuality_pipeline",
    sub_agents=[parallel_agent, combiner_agent],
    description="Runs parallel factor evaluation then combines into a single prediction.",
)

# -----------------------------------------------------------------------------
# App (for Runner and adk run)
# -----------------------------------------------------------------------------

PATTERNS = [
    "simple_prompt",
    "function_calling",
    "simple_plus_function",
    "basic_cot",
    "cot",  # full CoT prompt from src/cot_prompt.py (single source of truth)
    "fcot",  # full FCoT prompt from src/fcot_prompt.py (single source of truth)
    "complex_prompt",
]


def _instruction_simple(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""Score {factor_name} from 0-10 for this article. 0=low/neutral, 10=high.
Brief criteria: {recipe[:200]}...
Return ONLY valid JSON: {{"score": <0-10>, "explanation": "<short>"}}"""


def _instruction_with_tools(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""Score {factor_name} 0-10. Criteria: {recipe[:200]}...
You have Google Search - use it to verify factual claims when relevant.
Return ONLY JSON: {{"score": <0-10>, "explanation": "<short>"}}"""


def _instruction_basic_cot(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""Evaluate {factor_name} using chain-of-thought:
1. Identify evidence in the article
2. Evaluate against criteria
3. Synthesize into score 0-10
SCORING RECIPE: {recipe}
Return ONLY JSON: {{"score": <0-10>, "explanation": "<your step-by-step reasoning>"}}"""


def _instruction_complex(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""You are an expert fact-checker evaluating {factor_name}.
SCORING RECIPE:
{recipe}
Return ONLY valid JSON in this exact format:
{{"score": <number 0-10>, "explanation": "<string: detailed paragraph>"}}
Return ONLY the JSON object, nothing else."""


def _combiner_simple() -> str:
    return """Combine these factor scores into one prediction.
political_affiliation_bias: {political_affiliation_bias}
clickbait_level: {clickbait_level}
sensationalism: {sensationalism}
title_body_alignment: {title_body_alignment}
sentiment_bias: {sentiment_bias}
toxicity_level: {toxicity_level}
Output ONLY JSON: {"combined_veracity_score": <0-10>, "overall_assessment": "<string>"}
combined_veracity_score: 0=reliable, 10=unreliable."""


def _instruction_cot(factor_name: str, factor_key: str) -> str:
    """Full CoT prompt from src/cot_prompt.py (single source of truth)."""
    recipe = SCORING_RECIPES.get(factor_key, "")
    return get_cot_factor_instruction(factor_name, factor_key, recipe)


def _instruction_fcot(factor_name: str, factor_key: str) -> str:
    """Full FCoT prompt from src/fcot_prompt.py (single source of truth)."""
    recipe = SCORING_RECIPES.get(factor_key, "")
    return get_fcot_factor_instruction(factor_name, factor_key, recipe)


def _build_factor_agents(pattern: str):
    use_tools = pattern in ("function_calling", "simple_plus_function", "cot", "fcot")
    tools = GOOGLE_SEARCH_TOOL if use_tools else []
    if pattern == "simple_prompt":
        instr = _instruction_simple
    elif pattern in ("function_calling", "simple_plus_function"):
        instr = _instruction_with_tools
    elif pattern == "basic_cot":
        instr = _instruction_basic_cot
    elif pattern == "cot":
        instr = _instruction_cot
    elif pattern == "fcot":
        instr = _instruction_fcot
    elif pattern == "complex_prompt":
        instr = _instruction_complex
    else:
        instr = _instruction_simple
    agents = []
    for name, key, output_key in FACTUALITY_FACTORS:
        agents.append(
            LlmAgent(
                name=f"{key}_evaluator",
                model=MODEL,
                description=f"Evaluates {name}. Returns score 0-10.",
                instruction=instr(name, key),
                output_key=output_key,
                tools=tools,
            )
        )
    return agents


def create_app(pattern: str = None) -> App:
    """Create app. If pattern is None, returns the default full pipeline (all patterns)."""
    if pattern is None:
        return App(name="factuality_evaluator", root_agent=root_agent)
    if pattern not in PATTERNS:
        raise ValueError(f"pattern must be one of {PATTERNS}")
    if pattern == "cot":
        combiner_instr = _combiner_instruction_provider(get_cot_combiner_instruction())
    elif pattern == "fcot":
        combiner_instr = _combiner_instruction_provider(get_fcot_combiner_instruction())
    else:
        combiner_instr = _combiner_simple()
    factor_agents = _build_factor_agents(pattern)
    parallel = ParallelAgent(
        name="factuality_parallel",
        sub_agents=factor_agents,
        description="Evaluates six factuality factors.",
    )
    combiner = LlmAgent(
        name="combiner_agent",
        model=MODEL,
        description="Produces combined score from factor evaluations.",
        instruction=combiner_instr,
        output_key="combined_prediction",
    )
    root = SequentialAgent(
        name="factuality_pipeline",
        sub_agents=[parallel, combiner],
        description="Factor evaluation then combine.",
    )
    return App(name=f"factuality_evaluator_{pattern}", root_agent=root)


app = create_app()
