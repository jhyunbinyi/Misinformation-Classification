# Prompting Strategies

This document outlines each prompting strategy used in the factuality pipeline, with code excerpts and explanations. A comparison section at the end shows differences side-by-side with examples.

---

## Overview: How Prompting Works

1. **Single user message** — Every run uses the same user prompt, built in `src/run.py` by `build_prompt()`. It includes the article (title, URL, content) and optional predictive model probability vectors.
2. **Pattern selection** — When you create an app with `create_app(pattern="...")`, that pattern selects:
   - The **factor agent instruction** (what each of the six factor agents is told to do).
   - The **combiner instruction** (what the final combiner agent is told to do).
   - Whether factor agents get **Google Search** as a tool.
3. **Six factors** — Political Affiliation Bias, Clickbait Level, Sensationalism, Title–Body Alignment, Sentiment Bias, Toxicity Level. Each factor agent receives the same user message but its own instruction (and optionally the same scoring recipe).

---

## Shared Elements

### User prompt (same for all strategies)

Defined in `src/run.py`:

```python
def build_prompt(
    article_title: str,
    article_content: str,
    article_url: str = "",
    predictive_scores: Optional[Dict[str, Any]] = None,
) -> str:
    # ... builds scores_block if predictive_scores ...
    return f"""ARTICLE TO ANALYZE:
Title: {article_title}
URL: {article_url or "Not provided"}
Content: {article_content}
{scores_block}

Analyze this article according to your factuality factor and provide your evaluation."""
```

**What it does:** Supplies the article and optional classifier probabilities. Every factor agent and the combiner see this same text as the user message; the **instruction** (system-side) is what varies by strategy.

### Scoring recipes (shared across strategies)

Defined in `src/app.py` as `SCORING_RECIPES`. Each key (e.g. `political_affiliation`, `clickbait`) has a short rubric: scale meaning (0–10) and a numbered list of what to look for.

**Excerpt (political_affiliation):**

```python
"political_affiliation": """
    Score Political Affiliation Bias (0-10, where 0=neutral, 10=highly biased):
    1. Identify explicit mentions of political parties, candidates, or ideologies
    2. Assess the tone: neutral reporting (0-3), slight bias (4-6), strong bias (7-10)
    3. Look for loaded language, framing, or selective facts
    4. Consider whether both sides are presented fairly
    """,
```

**What it does:** Defines how to map evidence to a 0–10 score for that factor. Injected into factor instructions (in full or truncated) depending on the strategy.

---

## Strategy 1: Simple prompt

**Where:** `src/app.py` — `_instruction_simple`, `_combiner_simple()`  
**Tools:** None  
**Pattern name:** `simple_prompt`

### Factor instruction (excerpt)

```python
def _instruction_simple(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""Score {factor_name} from 0-10 for this article. 0=low/neutral, 10=high.
Brief criteria: {recipe[:200]}...
Return ONLY valid JSON: {{"score": <0-10>, "explanation": "<short>"}}"""
```

**What it does:** One short sentence: score 0–10, a truncated (200-char) slice of the recipe, and strict JSON output. No chain-of-thought, no search.

### Combiner (excerpt)

```python
def _combiner_simple() -> str:
    return """Combine these factor scores into one prediction.
political_affiliation_bias: {political_affiliation_bias}
...
Output ONLY JSON: {"combined_veracity_score": <0-10>, "overall_assessment": "<string>"}
combined_veracity_score: 0=reliable, 10=unreliable."""
```

**What it does:** Lists the six factor outputs (filled by ADK from state) and asks for one JSON with combined score and assessment. No explicit reasoning steps.

---

## Strategy 2: Function calling (tools, no CoT)

**Where:** `src/app.py` — `_instruction_with_tools`, `_combiner_simple()`  
**Tools:** Google Search  
**Pattern name:** `function_calling` or `simple_plus_function`

### Factor instruction (excerpt)

```python
def _instruction_with_tools(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""Score {factor_name} 0-10. Criteria: {recipe[:200]}...
You have Google Search - use it to verify factual claims when relevant.
Return ONLY JSON: {{"score": <0-10>, "explanation": "<short>"}}"""
```

**What it does:** Same minimal scoring + truncated recipe as simple, but adds one line: the model has Google Search and should use it when relevant. Still no structured chain-of-thought.

---

## Strategy 3: Basic chain-of-thought

**Where:** `src/app.py` — `_instruction_basic_cot`, `_combiner_simple()`  
**Tools:** None  
**Pattern name:** `basic_cot`

### Factor instruction (excerpt)

```python
def _instruction_basic_cot(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""Evaluate {factor_name} using chain-of-thought:
1. Identify evidence in the article
2. Evaluate against criteria
3. Synthesize into score 0-10
SCORING RECIPE: {recipe}
Return ONLY JSON: {{"score": <0-10>, "explanation": "<your step-by-step reasoning>"}}"""
```

**What it does:** Adds a generic three-step CoT (Identify → Evaluate → Synthesize) and the **full** scoring recipe. Asks for step-by-step reasoning in the explanation. No factor-specific wording and no search.

---

## Strategy 4: Full CoT (cot_prompt.py)

**Where:** `src/cot_prompt.py` — `COT_THREE_STEPS_BY_FACTOR`, `COT_FACTOR_INSTRUCTION`, `COT_COMBINER_INSTRUCTION`  
**Tools:** Google Search  
**Pattern name:** `cot`

### Factor structure (Identify → Evaluate → Synthesize, per factor)

Each factor has its own three-step block. Example for **political_affiliation**:

```python
# From src/cot_prompt.py
"political_affiliation": """
1. **Identify** — List concrete evidence in the article: mentions of parties,
   candidates, or ideologies; adjectives or framing that favor one side;
   sourcing that leans one way; whether counterpoints get space and fair tone.

2. **Evaluate** — For each piece of evidence, assess it against the scoring
   recipe. ... If you use Google Search to verify polls, votes, or policy
   claims, treat results as evidence and cite sources. Distinguish neutral
   reporting (low score) from framing that pushes a partisan reading (high).

3. **Synthesize** — Combine your evaluations into a single score (0–10) and a
   clear explanation that reflects this step-by-step reasoning.
""",
```

**What it does:** Factor-specific instructions for what to identify and how to evaluate (including when to use search and how to distinguish low vs high). Same Identify → Evaluate → Synthesize structure for all six, but wording is tailored per factor.

### Factor template (excerpt)

```python
# From src/cot_prompt.py
COT_FACTOR_INSTRUCTION = """You are an expert fact-checker evaluating {factor_name} \
in news articles. Use chain-of-thought reasoning before giving your final score.

## Your reasoning structure (Identify → Evaluate → Synthesize)

In your reasoning, explicitly follow these three steps for this factor:

{factor_three_steps}

## Scoring recipe for this factor

{recipe}
...
"""
```

**What it does:** Wraps the per-factor three steps and the scoring recipe in a single template; `get_cot_factor_instruction(factor_name, factor_key, recipe)` fills the placeholders.

### Combiner (excerpt)

```python
# From src/cot_prompt.py
1. **Identify** — Consider each factor output in turn:
   - political_affiliation_bias: {{...}}
   ...
   Note the score and key points from each explanation.

2. **Evaluate** — Weigh agreements and conflicts. ... Decide which factors
   should influence the overall veracity most for this article.

3. **Synthesize** — Combine your reasoning into a single combined_veracity_score
   (0–10, lower = more reliable) and a brief overall_assessment ...
```

**What it does:** Combiner uses the same Identify → Evaluate → Synthesize at document level: read the six outputs, weigh agreement/conflict, then produce combined score and assessment.

---

## Strategy 5: Full FCoT (fcot_prompt.py)

**Where:** `src/fcot_prompt.py` — `FCOT_THREE_STEPS_BY_FACTOR`, `FCOT_FACTOR_INSTRUCTION`, `FCOT_COMBINER_INSTRUCTION`  
**Tools:** Google Search  
**Pattern name:** `fcot`

### FCoT principles (from docstring)

- **Same structure at every scale:** Problem → Solution → **Verification** → Justification (explicit checkpoint at each level).
- **Optional recursion:** If the task is complex, break into 2–3 subgoals; for each, apply the same four steps; stop when a subgoal is straightforward.
- Recursive self-correction (maximize local goal, minimize error/bias).
- Aperture expansion (start narrow, then expand to search/scores).
- Temporal re-grounding (revise when new evidence contradicts).
- Inter-agent reflectivity (combiner reconciles factor outputs).
- Multi-scale coordination (factor = evidence-level; combiner = document-level).

### Factor structure (Problem → Solution → Verification → Justification, per factor)

Example for **political_affiliation**:

```python
# From src/fcot_prompt.py (four steps)
1. **Problem** — Goal for this level: evaluate political affiliation bias.
   Identify and list evidence... If complex, break into 2–3 sub-questions;
   for each, apply the same four steps.

2. **Solution** — Propose a score (0–10) and draft justification. Self-correct;
   if search contradicts your draft, revise (temporal re-grounding). Cite sources.

3. **Verification** — Check: Does your score match the recipe scale? Edge cases?
   Reasoning consistent? Revise if needed.

4. **Justification** — Synthesize (Problem → Solution → Verification →
   Justification). Optional: brief L0/L1 outline if you used subgoals.
```

**What it does:** Aligns with fractal CoT: **explicit Verification** step (constraints, edge cases, consistency); **optional recursion** (break into sub-questions, same four steps, stop when straightforward); narrow aperture and temporal re-grounding in Solution; layered objectives in the template.

### Combiner (excerpt)

```python
# From src/fcot_prompt.py (four steps)
1. **Problem** — Goal: combined veracity score. What do the six factors say?
   Agree or conflict? If complex, break into 2–3 sub-tasks and apply same steps.

2. **Solution** — Propose combined_veracity_score and draft assessment.
   Re-ground if factors conflict (inter-agent reflectivity).

3. **Verification** — Check: Score consistent with factor scores? Conflicts
   addressed? Edge cases? Revise if needed.

4. **Justification** — Synthesize into brief overall_assessment (Problem →
   Solution → Verification → Justification).
```

**What it does:** Same four-step fractal structure at document scale, with explicit Verification and optional sub-tasks; re-grounding and inter-agent reflectivity when factors conflict.

---

## Strategy 6: Complex prompt (no CoT structure)

**Where:** `src/app.py` — `_instruction_complex`, `_combiner_simple()`  
**Tools:** None  
**Pattern name:** `complex_prompt`

### Factor instruction (excerpt)

```python
def _instruction_complex(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""You are an expert fact-checker evaluating {factor_name}.
SCORING RECIPE:
{recipe}
Return ONLY valid JSON in this exact format:
{{"score": <number 0-10>, "explanation": "<string: detailed paragraph>"}}
Return ONLY the JSON object, nothing else."""
```

**What it does:** Expert role + full scoring recipe + request for a **detailed paragraph** explanation. No numbered steps or Identify/Evaluate/Synthesize (or Problem/Solution/Justification).

---

## Strategy 7: Default pipeline (no pattern)

**Where:** `src/app.py` — `_factor_instruction` (used by the six named factor agents), `combiner_agent`  
**Tools:** Google Search  
**Pattern name:** None (`create_app()` with no argument)

### Factor instruction (excerpt)

```python
def _factor_instruction(factor_name: str, factor_key: str) -> str:
    recipe = SCORING_RECIPES.get(factor_key, "")
    return f"""You are an expert fact-checker evaluating {factor_name} in news articles.

Use chain-of-thought reasoning before giving your final score. In your mind (or in your explanation), follow these steps:
1. Identify: List specific evidence in the article relevant to {factor_name} (quotes, phrases, structural choices).
2. Evaluate: For each piece of evidence, assess it against the scoring recipe below. ...
3. Synthesize: Combine your evaluations into a single score (0-10) and a clear explanation ...

SCORING RECIPE:
{recipe}

You have access to Google Search. When the article makes factual claims ..., use web search to verify them when it would affect your score or explanation. Cite sources when you use search results.
...
"""
```

**What it does:** One shared CoT (Identify → Evaluate → Synthesize) for all factors, full recipe, and explicit Google Search use + cite sources. No per-factor customization; same instruction shape for every factor.

### Combiner (excerpt)

```python
# combiner_agent in app.py
instruction="""You are the final step in a factuality pipeline. Use chain-of-thought reasoning before giving your combined prediction. Follow these steps in order:

1. Consider each factor in turn: Read political_affiliation_bias, then clickbait_level, ...
2. Weigh and reconcile: Identify where factors agree or conflict ...
3. Synthesize: Combine your reasoning into a single combined_veracity_score (0-10, lower = more reliable) and a brief overall_assessment ...
...
"""
```

**What it does:** Three-step combiner (consider each factor → weigh and reconcile → synthesize) with full placeholder list. No fractal or re-grounding language.

---

## Comparison: Differences With Examples

### CoT vs FCoT: How our implementations align with the usual framing

- **CoT** = “think step-by-step once, in one linear stream.”  
- **Fractal CoT (FCoT)** = “think step-by-step, but hierarchically and recursively (plan → solve → verify at multiple levels), like an outline that keeps nesting.”

| Aspect | CoT (our `cot` pattern) | FCoT (our `fcot` pattern) |
|--------|--------------------------|----------------------------|
| **Structure** | One sequence: Identify → Evaluate → Synthesize. No subgoal breakdown. | Same mini-pattern at every level: Problem → Solution → Verification → Justification. Optional tree: break into 2–3 subgoals, apply same four steps, optional L0/L1 outline. |
| **When it helps** | Suited to straightforward factor evaluation (one linear pass per factor). | Suited to complex or multi-part cases: prompts say “if this factor is complex, break into 2–3 sub-questions” and “if the picture is complex, break into 2–3 sub-tasks” at combiner. |
| **Error control** | No dedicated verification step; early mistakes can propagate. | Explicit **Verification** at each level (“check constraints, edge cases, consistency; revise if needed”), so errors are caught locally. |
| **Editability** | Single linear chain; revising usually means re-running or editing the whole explanation. | Optional L0/L1 hierarchy in the explanation supports editing one branch (e.g. one sub-question’s answer) without touching the rest. |
| **Token/cost** | Shorter: three steps, no decomposition or verification. | Can be longer: four steps plus optional subgoals and outline; verification adds checkpoint text. |

**Rule of thumb:** Use **CoT** when each factor is simple enough for a single Identify → Evaluate → Synthesize pass. Use **FCoT** when the article or the factor is multi-part, constraint-heavy, or when you want local verification and easier partial revision.

---

### 1. Step names and structure

| Strategy      | Factor steps                    | Combiner steps                          |
|---------------|----------------------------------|-----------------------------------------|
| simple        | (none; just “score 0–10”)        | (none; “combine into one prediction”)   |
| function_calling | (none; + “use Google Search”) | Same as simple                          |
| basic_cot     | Identify → Evaluate → Synthesize | Same as simple                          |
| **cot**       | **Identify → Evaluate → Synthesize** (per-factor text) | **Identify → Evaluate → Synthesize** (over six outputs) |
| **fcot**      | **Problem → Solution → Verification → Justification** (per-factor + optional subgoals, self-correct, re-ground) | **Same four steps** (re-ground, inter-agent reflectivity) |
| complex       | (none; “detailed paragraph”)     | Same as simple                          |
| default       | Identify → Evaluate → Synthesize (shared) | Consider → Weigh and reconcile → Synthesize |

### 2. Example: Factor instruction for “Political Affiliation Bias”

**Simple (minimal):**
```text
Score Political Affiliation Bias from 0-10 for this article. 0=low/neutral, 10=high.
Brief criteria: Score Political Affiliation Bias (0-10, where 0=neutral...
Return ONLY valid JSON: {"score": <0-10>, "explanation": "<short>"}
```

**Basic CoT (generic three steps):**
```text
Evaluate Political Affiliation Bias using chain-of-thought:
1. Identify evidence in the article
2. Evaluate against criteria
3. Synthesize into score 0-10
SCORING RECIPE: [full recipe]
Return ONLY JSON: {"score": <0-10>, "explanation": "<your step-by-step reasoning>"}
```

**CoT (from cot_prompt.py — factor-specific):**
```text
... Use chain-of-thought reasoning before giving your final score.

## Your reasoning structure (Identify → Evaluate → Synthesize)
1. **Identify** — List concrete evidence in the article: mentions of parties,
   candidates, or ideologies; adjectives or framing that favor one side; ...
2. **Evaluate** — For each piece of evidence, assess it against the scoring
   recipe. ... If you use Google Search to verify polls, votes, or policy
   claims, treat results as evidence and cite sources. Distinguish neutral
   reporting (low score) from framing that pushes a partisan reading (high).
3. **Synthesize** — Combine your evaluations into a single score (0–10) and a
   clear explanation that reflects this step-by-step reasoning.

## Scoring recipe for this factor
[full recipe]
```

**FCoT (from fcot_prompt.py — four steps + optional subgoals):**
```text
1. **Problem** — Goal: evaluate political affiliation bias. Identify and list
   evidence... If complex, break into 2–3 sub-questions; apply same four steps.

2. **Solution** — Propose score (0–10) and draft justification. Self-correct; if
   search contradicts draft, revise (temporal re-grounding). Cite sources.

3. **Verification** — Check: score on 0–10? Edge cases? Reasoning consistent?
   Revise if needed.

4. **Justification** — Synthesize (Problem → Solution → Verification →
   Justification). Optional: brief L0/L1 outline if you used subgoals.
```

### 3. Tools (Google Search)

| Strategy        | Factor agents have search? |
|-----------------|----------------------------|
| simple_prompt   | No                         |
| function_calling, simple_plus_function | Yes                |
| basic_cot      | No                         |
| **cot**        | **Yes**                    |
| **fcot**       | **Yes**                    |
| complex_prompt  | No                         |
| default         | Yes                        |

### 4. Where the prompt text lives

| Strategy     | Factor instruction source     | Combiner source        |
|-------------|--------------------------------|------------------------|
| simple, function_calling, basic_cot, complex | Inline in `app.py` (`_instruction_*`) | Inline in `app.py` (`_combiner_*`) |
| **cot**     | **`src/cot_prompt.py`** (`COT_THREE_STEPS_BY_FACTOR` + `COT_FACTOR_INSTRUCTION`) | **`src/cot_prompt.py`** (`COT_COMBINER_INSTRUCTION`) |
| **fcot**    | **`src/fcot_prompt.py`** (`FCOT_THREE_STEPS_BY_FACTOR` + `FCOT_FACTOR_INSTRUCTION`) | **`src/fcot_prompt.py`** (`FCOT_COMBINER_INSTRUCTION`) |
| default     | `app.py` (`_factor_instruction`) | `app.py` (`combiner_agent.instruction`) |

---

## How to use a strategy

Pass the pattern when creating the app, then run with that app:

```python
from src.app import create_app
from src import run

app = create_app(pattern="cot")   # or "fcot", "simple_prompt", "basic_cot", etc.
result = await run(
    article_title="...",
    article_content="...",
    article_url="...",
    app_instance=app,
)
```

The default app (used when you call `run()` without `app_instance`) is the **default pipeline** (strategy 7), not `cot` or `fcot`.
