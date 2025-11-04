# RAG News Agents

**Two-agent pipeline that converts news summaries → sector/ticker sentiment → price-direction (UP / DOWN / NO_IMPACT)** with integrated RAG (Retrieval-Augmented Generation) capabilities.

## 🚀 Key Features

- **Agent-1** (LLM): Maps each news item to sector/tickers and assigns a signed **sentiment_score** in `[-4.0, +4.0]`, with confidence, horizon, news type, and evidence phrases.
- **Agent-1 Aggregation** (programmatic): Handles **many stories on the same day** for the same sector, weights by confidence/news-type, and **calibrates** to the next-day sector % change (if provided).
- **Agent-2** (programmatic): Aggregates adjusted sentiments into a **final label** (UP/DOWN/NO_IMPACT) using weighted mean + consensus thresholds.
- **RAG Integration**: Built-in RAG API client for fetching real-time news data from external vector databases.
- **Automated Pipeline**: Complete end-to-end pipeline from news fetching to HTML report generation.
- **Enhanced Reporting**: Beautiful HTML reports with sector-wise impact indicators and news context.

---

## Table of Contents
- [Quickstart](#quickstart)
- [CLI Usage](#cli-usage)
- [Data Formats](#data-formats)
- [Architecture](#architecture)
- [Configuration & Few-Shots](#configuration--few-shots)
- [Integrate With Your RAG](#integrate-with-your-rag)
- [RAG Pipeline Integration](#rag-pipeline-integration)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Quickstart

> This folder is vendored inside the FinBERT News RAG application. No additional clone is required—start from the repository root and follow the steps below.

### 1) Enter the agents workspace
```bash
cd agents/sector_news_analysis
```

### 2) Python venv (Mac/Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> If your prompt shows `(.venv) (base)`, run `conda deactivate` until `(base)` disappears, then `source .venv/bin/activate` again.

### 3) Install dependencies
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> The agents will call the FinBERT RAG API by default. Configure one of the following environment variables before running the pipeline:
>
> ```
> export FINBERT_RAG_BASE_URL="http://localhost:8000"        # default local API
> # or use SECTOR_AGENT_RAG_BASE_URL to override only the agents
> export SECTOR_AGENT_RAG_BASE_URL="https://your-prod-alb.amazonaws.com"
> ```
> The search endpoint defaults to `/search/cosine/embedding1155d/`. Override with `SECTOR_AGENT_RAG_ENDPOINT` if you need a different embedding route.
> If you see a Typer/Click help error about `make_metavar(ctx)`, pin Click and reinstall:
> ```bash
> echo 'click==8.1.7' >> requirements.txt
> python -m pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
> ```

### 4) Set your OpenAI key (optional for mock run)
Create a **plain-text** `.env` in the project root:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
> Don’t paste RTF. If your key is in an `.rtf`, convert it:  
> `textutil -convert txt OPENAI_API_KEY.rtf -output OPENAI_API_KEY.txt`

### 5) Make the code importable
```bash
export PYTHONPATH="$PWD/src"
```

### 6) Run the demo

**Mock LLM (no API needed):**
```bash
python -m news_agents.cli agent1-run --news data/examples/telecom_news.json --sector-map data/examples/sector_map.json --market IN --provider mock --out .cache/agent1.json

python -m news_agents.cli agent1-aggregate --agent1-json .cache/agent1.json --next-day data/examples/next_day_changes.json --out .cache/agent1_adjusted.json

python -m news_agents.cli agent2-decide --agent1-json .cache/agent1_adjusted.json --level sector --name Telecom --out .cache/decision_telecom.json
cat .cache/decision_telecom.json
```

**OpenAI LLM (requires `.env`):**
```bash
python -m news_agents.cli agent1-run --news data/examples/telecom_news.json --sector-map data/examples/sector_map.json --market IN --provider openai --out .cache/agent1_openai.json

python -m news_agents.cli agent1-aggregate --agent1-json .cache/agent1_openai.json --next-day data/examples/next_day_changes.json --out .cache/agent1_adjusted.json

python -m news_agents.cli agent2-decide --agent1-json .cache/agent1_adjusted.json --level sector --name Telecom --out .cache/decision_telecom.json
cat .cache/decision_telecom.json
```

---

## CLI Usage

### 1) Agent-1 — score news
```
python -m news_agents.cli agent1-run --news PATH --sector-map PATH --market IN|GLOBAL --provider mock|openai --out PATH
```
- `--news`: JSON list of news (see formats below)
- `--sector-map`: sector → tickers mapping
- `--provider`: `mock` (deterministic demo) or `openai`
- Writes an array of Agent-1 records

### 2) Aggregation & calibration
```
python -m news_agents.cli agent1-aggregate --agent1-json PATH --next-day PATH --out PATH
```
- Groups by `(sector, date_key)`
- Weights stories by confidence × magnitude × news-type multiplier
- Calibrates day score to **next-day sector % change** if provided
- Writes **per-story** adjusted sentiments

### 3) Agent-2 — final label
```
python -m news_agents.cli agent2-decide --agent1-json PATH \
  --level sector --name <SectorName> \
  [--start_date YYYY-MM-DD --end_date YYYY-MM-DD] \
  [--up_threshold 0.8 --down_threshold -0.8 --min_consensus 0.6] \
  --out PATH
```
Or for tickers:
```
python -m news_agents.cli agent2-decide --agent1-json PATH \
  --level tickers --tickers TICK1,TICK2 \
  --out PATH
```
Output JSON:
```json
{
  "label": "UP",
  "weighted_mean": 1.18,
  "consensus": 0.72,
  "confidence": 0.81,
  "rationale": "Direction inferred from weighted mean and consensus of adjusted sentiment.",
  "top_signals": ["N_te_1","N_te_3","N_te_2"],
  "target": {"level":"sector","name":"Telecom","tickers":[]}
}
```

---

## Data Formats

### `--news` (array of objects)
```json
[
  {
    "id": "N_te_1",
    "headline": "TRAI trims 5G reserve prices by 18%",
    "summary": "Regulator cuts reserve prices to accelerate 5G adoption.",
    "datetime": "2025-09-26T10:15:00Z",
    "source": "Economic Daily",
    "region": "IN"
  }
]
```

### `--sector-map`
```json
{
  "Telecom": ["BHARTIARTL.NS", "RELIANCE.NS"],
  "Pharmaceuticals": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS"]
}
```

### `--next-day` (sector,YYYY-MM-DD → % move)
```json
{
  "(Telecom,2025-09-26)": 1.2
}
```

---

## Architecture

```
src/news_agents/
├── agent1.py          # LLM call + same-day aggregation + calibration
├── agent2.py          # final decision using weighted mean + consensus
├── cli.py             # Typer-based CLI commands
├── config.py          # system prompts + few-shots
├── llm.py             # 'mock' and 'openai' providers
└── types.py           # NewsItem, Agent1Record, helpers
```

### Agent-1 (LLM)
- System prompt turns each **news item** into 1+ `(sector, tickers)` records with:
  - `sentiment_score ∈ [-4, +4]`
  - `confidence ∈ [0,1]`
  - `impact_horizon` (intraday/short/medium)
  - `news_type` (regulatory, legal, earnings, etc.)
  - `evidence_phrases` (verbatim snippets)
- Few-shot examples live in `config.py`.

### Same-Day Aggregation
- For each `(sector, date)`:
  - weight per story = `confidence × magnitude × news_type_multiplier`
  - **day_score_raw** = weighted average of sentiments
  - If `next_day % change` exists and **sign matches**, scale the day score into **day_score_calibrated** and **redistribute** back to each story as `adjusted_sentiment`.

### Agent-2 (Programmatic)
- For the target (sector or tickers), compute:
  - `weighted_mean` = Σ(w*s)/Σ(w), where `w = confidence × recency_decay`
  - `consensus` = fraction of weight aligned with the sign of `weighted_mean`
- Decision rules (defaults):  
  - `UP` if `weighted_mean ≥ 0.8` and `consensus ≥ 0.6`  
  - `DOWN` if `weighted_mean ≤ -0.8` and `consensus ≥ 0.6`  
  - else `NO_IMPACT`

---

## Configuration & Few-Shots
- Tune prompts and examples in `src/news_agents/config.py`.
- Adjust news-type multipliers in `src/news_agents/agent1.py` (`NEWS_TYPE_MULTIPLIER`).
- Tune Agent-2 thresholds via CLI flags:
  - `--up_threshold`, `--down_threshold`, `--min_consensus`.

---

## Integrate With Your RAG
You already have 100k news summaries and sector keywords. Plug them into Agent-1 like this:

1. **Build the `--news` JSON** your retriever returns for a given day/sector.
2. Run Agent-1 (OpenAI or your preferred provider).
3. Feed **Agent-1 JSON** into `agent1-aggregate` with a daily sector move file (optional).
4. Use `agent2-decide` to get the final label.

**Programmatic use (inside Python):**
```python
from news_agents.types import NewsItem
from news_agents.agent1 import Agent1
from news_agents.agent2 import Agent2

items = [NewsItem(...), ...]
sector_map = {"Telecom": ["BHARTIARTL.NS", "RELIANCE.NS"]}
a1 = Agent1(provider="openai")  # or "mock"
recs = a1.run_llm(items, sector_map, market="IN")

# optional aggregation step:
daywise = a1.process_batch(recs, next_day_sector_change={("Telecom","2025-09-26"): 1.2})
adjusted = [r for blob in daywise.values() for r in blob["records"]]

a2 = Agent2()
decision = a2.decide([r for r in adjusted if r.sector == "Telecom"])
print(decision)
```

---

## RAG Pipeline Integration

The project now includes a complete **RAG (Retrieval-Augmented Generation) pipeline** that automates the entire process from news fetching to final report generation.

### 🚀 Complete Pipeline Execution

**Run the full RAG pipeline:**
```bash
# Using mock provider (no API keys needed)
python scripts/run_rag_pipeline.py --provider mock --output-report reports/rag_sector_analysis_report.html

# Using OpenAI provider (requires .env with OPENAI_API_KEY)
python scripts/run_rag_pipeline.py --provider openai --output-report reports/rag_sector_analysis_report.html

# Skip RAG search and use sample data
python scripts/run_rag_pipeline.py --provider mock --skip-rag --output-report reports/sample_analysis_report.html
```

**What the pipeline does:**
1. **RAG Search**: Fetches sector-specific news using the external RAG API
2. **Agent-1 Analysis**: Processes news through LLM for sentiment analysis
3. **Agent-1 Aggregation**: Calibrates and aggregates sentiments by sector/date
4. **Agent-2 Decisions**: Generates UP/DOWN/NO_IMPACT labels for each sector
5. **HTML Report**: Creates beautiful reports with impact indicators and news context

### 🔧 RAG API Client

**Standalone RAG data fetching:**
```bash
# Fetch news for specific sectors
python -m src.news_agents.rag_api_client --output .cache/news_rag.json --max-per-query 10 --sectors Banks Energy IT

# Fetch all sectors with custom parameters
python -m src.news_agents.rag_api_client --output .cache/news_all_rag.json --min-score 0.7 --max-per-query 15
```

**RAG Configuration (`rag_config.json`):**
```json
{
  "base_url": "http://your-rag-endpoint.com",
  "endpoint": "/search/cosine/embedding768d/",
  "min_score": 0.5,
  "max_results_per_query": 25,
  "max_results_per_sector": 25,
  "timeout": 30,
  "region": "IN",
  "retry_attempts": 3,
  "rate_limit_delay": 1.0
}
```

### 📊 Recent Execution Results

**Latest RAG Pipeline Run:**
- **Sectors Analyzed**: Banks, Energy
- **News Items Processed**: 50 total (25 per sector)
- **Results**:
  - Banks: `NO_IMPACT` (confidence: 0.2, weighted_mean: 0.0)
  - Energy: `NO_IMPACT` (confidence: 0.2, weighted_mean: 0.0)
- **Output**: `reports/rag_sector_analysis_report.html`

### 🎨 Enhanced HTML Reports

The pipeline generates beautiful, interactive HTML reports featuring:
- **Sector-wise impact indicators** (UP/DOWN/NO_IMPACT with color coding)
- **Confidence scores and rationale** for each decision
- **Original news context** with headlines, summaries, and sources
- **Weighted sentiment analysis** details
- **Exportable results** for further analysis

**View latest report:**
```bash
open reports/rag_sector_analysis_report.html
```

---

## Troubleshooting

- **Typer / Click help error (`make_metavar(ctx)`)**  
  Pin Click and reinstall:
  ```bash
  echo 'click==8.1.7' >> requirements.txt
  python -m pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
  ```

- **`ModuleNotFoundError: news_agents`**  
  You didn’t set `PYTHONPATH`:
  ```bash
  export PYTHONPATH="$PWD/src"
  ```

- **401 Unauthorized (OpenAI)**  
  - `.env` must be: `OPENAI_API_KEY=sk-proj-...` (plain text).  
  - RTF files won’t work; convert and copy from `.txt`.  
  - Quick key check:
    ```bash
    KEY=$(sed -n 's/^OPENAI_API_KEY=//p' .env | head -1)
    curl -s -o /dev/null -w "%{http_code}\n" https://api.openai.com/v1/models -H "Authorization: Bearer $KEY"
    ```
    Expect **200**.

- **Both `(.venv)` and `(base)` shown**  
  `conda deactivate` until `(base)` disappears, then `source .venv/bin/activate`.

- **macOS: `fork: Resource temporarily unavailable`**  
  Close extra Terminal sessions or reboot. (Files are already created; you don’t need to rerun the bootstrap.)

---

## FAQ

**Q: Can I run fully offline?**  
A: Yes, use `--provider mock` for Agent-1. Aggregation & Agent-2 are pure Python.

**Q: How do I change the sentiment scale or thresholds?**  
A: Edit the prompts in `config.py` and Agent-2 flags (`--up_threshold`, `--down_threshold`, `--min_consensus`).

**Q: How do I target specific tickers instead of the whole sector?**  
A: Use `--level tickers --tickers TICK1,TICK2` in `agent2-decide`.

---

## Roadmap
- Sector-specific calibration & priors
- Backtesting + metrics (precision/recall on UP/DOWN)
- Streamlit dashboard to inspect attributions
- Pydantic validation of inputs/outputs
- Async batch runner for large daily backfills

---

## Contributing
Issues and PRs welcome. Please don’t commit secrets. The `.env` is ignored via `.gitignore`.

---

## License
MIT
