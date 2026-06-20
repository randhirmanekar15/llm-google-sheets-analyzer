# LLM Google Sheets Analyzer

Pull live Google Sheets data, clean it deterministically in Python, then let a local LLM do the one thing it's good at: find patterns. **The model never does the math** — deterministic code sorts and slices; the LLM only interprets a clean, pre-computed top-N.

Runs locally on [Ollama](https://ollama.com).

## Stack

| Piece | Choice |
|-------|--------|
| Sheets API | `gspread` + `google-auth` |
| Cleaning | pandas |
| LLM runtime | Ollama (local) |
| Model | `llama3` |

## Setup

1. Google Cloud: create a project, enable the Sheets + Drive APIs, create a **service account**, download its JSON key, and share your sheet with the service-account email.
2. Install and pull the model:

```bash
ollama pull llama3
pip install -r requirements.txt
```

3. Set env vars (never hardcode the key path):

```bash
export GSHEET_CREDS=/path/to/service_account.json
export SHEET_ID=your_sheet_id
export METRIC="Hours Viewed"
```

## Usage

```bash
python analyzer.py
```

## Test

```bash
pip install pytest
pytest        # deterministic helpers, no network
```

## Security

The service-account JSON is a credential — scope it to one sheet, rotate it, and never commit it (`.gitignore` already excludes `service_account*.json` and `credentials*.json`).

## Limitations

- The LLM hallucinates trends on thin data (<~20 rows).
- Sheets API rate limits + local latency make this a batch/report tool, not a live dashboard.

---

Inspired by Aman Kharwal's tutorial, [Connect Your LLM to Google Sheets](https://amanxai.com/2026/04/26/connect-your-llm-to-google-sheets/). Rebuilt and extended (env-based secrets, parameterized metric, swappable model).

MIT licensed.
