# Capstone-A1

**Factuality assessment for news articles** — a multi-agent pipeline using Google ADK and Gemini to score articles on six factors and produce a combined veracity assessment.

---

## Features

- **Six factuality factors**: Political affiliation bias, clickbait, sensationalism, title–body alignment, sentiment bias, toxicity
- **Pipeline**: Six parallel LLM factor agents → combiner agent → single combined score (0–10) and narrative assessment
- **Optional predictive models**: Train sklearn classifiers from `data/` and feed probability vectors into the prompt for richer context
- **Interfaces**: Streamlit UI and Python API

## Requirements

- Python ≥3.8
- [Google AI API key](https://aistudio.google.com/app/apikey) (set `GOOGLE_API_KEY` or `GEMINI_API_KEY` in `.env`)

## Quick start

```bash
# Clone and install
git clone <repo-url>
cd Capstone-A1
pip install -e .

# Configure (create .env in project root)
echo "GOOGLE_API_KEY=your_key_here" > .env

# Run the Streamlit app
streamlit run app.py
```

Or run the CLI example:

```bash
python example.py
```

## Project layout

```
Capstone-A1/
├── src/                  # Package + scripts + tests
│   ├── app.py            # Agents, recipes, ADK App
│   ├── run.py            # Session, Runner, run()
│   ├── models.py         # get_predictive_scores()
│   ├── scripts/          # Training and utilities
│   │   ├── train_predictive_models.py
│   │   └── check_labels.py
│   └── tests/
├── data/                 # Datasets (see data/README.md)
├── app.py                # Streamlit entrypoint
├── example.py            # Script entrypoint
├── pyproject.toml
└── README.md
```

## Usage

**Streamlit:** `streamlit run app.py` — enter title and content, then Evaluate.

**Python API:**

```python
import asyncio
from src import run, get_predictive_scores

async def main():
    scores = get_predictive_scores(title, content, url)  # optional
    result = await run(
        article_title=title,
        article_content=content,
        article_url=url,
        predictive_scores=scores,
    )
    print(result["combined_veracity_score"], result["overall_assessment"])

asyncio.run(main())
```

## Predictive models (optional)

To attach classifier probability vectors to the pipeline:

```bash
python src/scripts/train_predictive_models.py   # writes data/models/*.joblib
```

Requires data under `data/` (tsv, clickbait, tox-new, pol-new, articles_labeled.csv). If no models exist, the app still runs; scores are omitted.

## Testing

```bash
pytest
```

Dataset layout and licenses: [data/README.md](data/README.md).

---

## License

See [LICENSE](LICENSE). Data under `data/` may have separate terms (see data/LICENSE).
