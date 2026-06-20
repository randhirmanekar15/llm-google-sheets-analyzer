# LLM Google Sheets Analyzer

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue) ![License: MIT](https://img.shields.io/badge/License-MIT-green) ![Runs 100% Local](https://img.shields.io/badge/LLM-100%25%20local-orange)

**Pull live Google Sheets data, clean it deterministically in Python, then let a local LLM find patterns — the model never does the math.**

## Overview

AI agents are creeping into the tools people already live in: spreadsheets, CRMs, ticket queues. That's exciting and dangerous in equal measure. The moment you hand a language model a raw column of numbers and ask "what's the trend?", you've quietly trusted it to count, sort, and compare — three things LLMs are famously bad at and confidently wrong about.

This project takes the opposite stance. The design rule is a hard split: **deterministic code does the math, the LLM does the interpretation.** Python loads the sheet, coerces types, drops the garbage, sorts by your metric, and slices a clean top-N. Only then does the model get involved — and all it's asked to do is recognize patterns in data that's already correct. The model never counts. It never sorts. It reads a pre-computed, trustworthy summary and tells you what it means.

That separation is the whole point. It's the difference between a demo that hallucinates a 30% revenue spike that isn't there, and a report you'd actually paste into a Monday standup. Treat the LLM as a junior analyst who's great at narrative and terrible at arithmetic, and build the pipeline so it never has to do arithmetic.

## Features

- **Live Google Sheets ingestion** via the Sheets API (`gspread` + `google-auth`).
- **Deterministic cleaning** — numeric coercion, null handling, and type fixing happen in pandas, not in the prompt.
- **Pre-computed top-N** — sorting and slicing by your chosen metric are done in code.
- **Fully local inference** — runs against Ollama (`llama3` by default); no data leaves your machine.
- **Swappable model** — change `OLLAMA_MODEL` to point at any model your Ollama instance serves.
- **Parameterized metric** — analyze whatever column matters via the `METRIC` env var, no code edits.
- **Credentials via env vars** — nothing sensitive is hardcoded or committed.

## How it works

1. **Load** — `load_sheet()` authenticates with the service-account JSON and pulls the sheet into a DataFrame.
2. **Clean** — `clean_numeric()` coerces the metric column to numbers and fixes types deterministically.
3. **Sort & slice** — the cleaned frame is sorted by `METRIC` and reduced to a top-N. The part you do *not* trust to a model.
4. **Interpret** — `query_llm()` sends the clean, ranked summary to Ollama and asks only for pattern recognition.

```
┌──────────────┐  gspread   ┌──────────────┐  clean_numeric  ┌──────────────┐
│ Google Sheet │ ─────────▶ │ pandas frame │ ──────────────▶ │  typed/clean │
└──────────────┘ Sheets API └──────────────┘                 └──────┬───────┘
                                                                     │ sort by METRIC
                                                                     ▼ slice top-N
                                                          ┌───────────────────┐
                                                          │  deterministic     │
                                                          │  top-N summary     │
                                                          └─────────┬─────────┘
                                                                    │ prompt
                                                                    ▼
                                                          ┌───────────────────┐
                                                          │  Ollama (llama3)   │
                                                          │  pattern recog.    │
                                                          └─────────┬─────────┘
                                                                    ▼
                                                              insights
```

The model only ever sees step 4's input. It never does the counting in steps 1–3.

## Tech stack

| Layer | Tool | Why |
|-------|------|-----|
| Sheets access | `gspread` + `google-auth` | Authenticated read of live Google Sheets |
| Data wrangling | `pandas` | Deterministic typing, cleaning, sorting, slicing |
| LLM transport | `requests` | Thin HTTP calls to the local Ollama API |
| Inference | Ollama (`llama3`) | 100% local pattern recognition, no data egress |
| Language | Python 3.10+ | — |

## Project structure

```
llm-google-sheets-analyzer/
├── analyzer.py        # load_sheet, clean_numeric, query_llm, analyze
├── test_analyzer.py   # unit tests for the deterministic helpers
├── ARTICLE.md
├── requirements.txt
├── LICENSE            # MIT
└── README.md
```

## Installation

```bash
git clone https://github.com/randhirmanekar15/llm-google-sheets-analyzer.git
cd llm-google-sheets-analyzer
pip install -r requirements.txt
ollama pull llama3
```

**Google Cloud setup:**

1. In the [Google Cloud Console](https://console.cloud.google.com/), create/pick a project.
2. Enable the **Google Sheets API** and **Google Drive API**.
3. Create a **service account**, then a **JSON key** for it, and download it (keep it out of version control).
4. **Share** your target sheet with the service-account email as a Viewer.
5. Grab the **Sheet ID** from the URL: `.../spreadsheets/d/`**`SHEET_ID`**`/edit`.

## Usage

```bash
export GSHEET_CREDS="/secure/path/service-account.json"
export SHEET_ID="1AbCdEf...your_sheet_id"
export METRIC="revenue"
python analyzer.py
```

PowerShell:

```powershell
$env:GSHEET_CREDS="C:\secure\service-account.json"; $env:SHEET_ID="..."; $env:METRIC="revenue"; python analyzer.py
```

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GSHEET_CREDS` | Yes | — | Absolute path to the service-account JSON key |
| `SHEET_ID` | Yes | — | The Google Sheet ID from its URL |
| `METRIC` | No | `Hours Viewed` | Column to sort/slice and analyze |
| `OLLAMA_MODEL` | No | `llama3` | Ollama model used for pattern recognition |
| `OLLAMA_URL` | No | `http://localhost:11434/api/generate` | Ollama generate endpoint |

## Security

The service-account JSON is a real credential — anyone holding it can read every sheet shared with that account.

- **Never commit it** (the filename is already in `.gitignore`).
- **Pass it by path** via `GSHEET_CREDS` — never hardcoded.
- **Scope it tight** — read-only, only the sheets it needs.
- **Rotate keys** periodically; prefer a secret manager in shared environments.

## Testing

```bash
pip install pytest
pytest
```

`test_analyzer.py` covers the deterministic core — numeric coercion, junk handling, and the sort/slice path — so the parts the model is *not* allowed to do stay provably correct.

## Limitations

- **The JSON key is a credential.** Scope it, rotate it, never commit it.
- **LLMs hallucinate trends on thin data** (< ~20 rows). Treat low-row output as suggestive.
- **Not a live dashboard.** Sheets API rate limits + local latency make this a batch/report tool.

## Roadmap

- [ ] Output structured JSON insights alongside the prose summary
- [ ] Support multiple metrics in a single run
- [ ] Write results back to an "Analysis" tab in the sheet
- [ ] CLI flags as an alternative to env vars
- [ ] Confidence flag when row count is below the thin-data threshold

## Credits

📖 Full write-up: [ARTICLE.md](ARTICLE.md).

Based on Aman Kharwal's tutorial, ["Connect Your LLM to Google Sheets"](https://amanxai.com/2026/04/26/connect-your-llm-to-google-sheets/).

**What I changed vs the source tutorial:**

- Moved credentials out of source and into environment variables.
- Parameterized the analyzed metric so any column can be targeted without code edits.
- Made the model swappable via `OLLAMA_MODEL`.

## Author

Built by **Randhir Manekar** — [randhirmanekar.com](https://randhirmanekar.com) · [github.com/randhirmanekar15](https://github.com/randhirmanekar15)

## License

MIT — see [LICENSE](LICENSE).
