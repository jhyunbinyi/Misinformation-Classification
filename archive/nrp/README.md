# Archived NRP Code

This folder contains the **NRP (Nautilus Research Platform)** evaluator code, archived because the project now uses **Google ADK + Gemini** only.

## Contents

- **multi_agent_evaluator_nrp.py** – NRP Basic CoT evaluator (6 parallel factors)
- **multi_agent_evaluator_nrp_function.py** – NRP Function Calling evaluator
- **test_nrp_evaluator.py** – Test script for Basic CoT
- **test_nrp_evaluator_function.py** – Test script for Function Calling
- **evaluate_nrp_model_performance.py** – Performance evaluation on labeled dataset (Basic CoT)
- **evaluate_nrp_model_performance_function.py** – Performance evaluation (Function Calling)

## How to run (from project root)

Requires `NRP_API_KEY` or `OPENAI_API_KEY` in `.env`. Data paths (e.g. `data/articles_labeled.csv`) are relative to the current working directory, so run from the **project root**:

```bash
# Tests
python archive/nrp/test_nrp_evaluator.py
python archive/nrp/test_nrp_evaluator_function.py

# Performance evaluation
python archive/nrp/evaluate_nrp_model_performance.py --max-articles 10
python archive/nrp/evaluate_nrp_model_performance_function.py --max-articles 10
```

The archived modules import `src.scoring_recipes` from the main repo, so the project root must be on `PYTHONPATH` (which the scripts set automatically when run as above).
