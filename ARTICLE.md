# I Wired a Local LLM Into Google Sheets — and Refused to Let It Do Math

*A hybrid pipeline that pulls live sheet data, cleans it in Python, and lets a local llama3 do the one thing it's actually good at: finding patterns.*

## Why this, why now

Every operations tool you touch in 2026 is sprouting an AI agent. Sales CRMs, admin dashboards, reporting decks — Google's own [AI agent trends report](https://cloud.google.com/resources/content/ai-agent-trends-2026) frames this as agents moving out of the chat window and into the boring everyday tools where work actually happens.

Good. But most of these integrations make the same mistake: they hand the LLM a spreadsheet and ask it to "analyze the numbers." Then the LLM confidently sums a column wrong and nobody notices until a board meeting.

Here's my design rule, and the whole point of this project: **let deterministic code do the math and the sorting. Let the LLM do the pattern recognition.** Don't make the model count. It's bad at counting and great at noticing "your top performers all signed up in Q1." Split the job along that line and the thing becomes trustworthy.

## What it does

The pipeline is four steps, runs entirely on my machine:

1. Pulls live rows from a Google Sheet over the API.
2. Cleans them deterministically in pandas — strips junk, fixes types, parses dates.
3. Sorts by whatever metric I care about and slices the top 10.
4. Feeds *only that clean slice* to a local llama3 and asks for trends — five bullets, no fluff.

No data leaves the laptop except the auth handshake. No OpenAI bill. No "the LLM did the arithmetic" risk, because the LLM never touches the arithmetic.

## The stack

| Layer | Tool | Job |
|---|---|---|
| Sheets API | `gspread` + `google-auth` | Read live rows |
| Cleaning | `pandas` | Deterministic typing, sorting, slicing |
| LLM runtime | Ollama (local) | Serve the model on `localhost:11434` |
| Model | `llama3` | Pattern recognition only |
| Glue | `requests` | POST the prompt to Ollama |

## How it works

First, auth and load. A service-account JSON gives `gspread` read access; I pull the whole sheet into a DataFrame in one shot.

```python
import os, gspread, pandas as pd
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    os.environ["GSHEET_CREDS"], scopes=SCOPES
)
client = gspread.authorize(creds)

sheet = client.open_by_key(os.environ["SHEET_ID"]).sheet1
df = pd.DataFrame(sheet.get_all_records())
```

Then the cleaning — `"1,250"` becomes `1250`, dates become real datetimes. Boring, deterministic, exactly what code should own.

Now the hybrid step, where the discipline lives. I sort and slice in pandas, then hand the LLM a tidy text table and a tight prompt.

```python
import requests

def query_llm(prompt: str) -> str:
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    return r.json()["response"]

top = df.sort_values(METRIC, ascending=False).head(10)

prompt = f"""You are a data analyst. Below are the top 10 rows by {METRIC}.
Do NOT recalculate any numbers — trust them.
Find patterns and trends. Max 5 bullets.

{top.to_string(index=False)}"""

print(query_llm(prompt))
```

Read the prompt again: *do not recalculate any numbers.* The sort already happened in pandas. The model's only job is to look at ten clean rows and tell me what they have in common.

## What I changed

I didn't copy the tutorial — I hardened it for actual reuse.

- **Credentials out of the code.** The original hardcodes a JSON path. I moved it to `GSHEET_CREDS` and `SHEET_ID` env vars so nothing secret lives in the repo. Non-negotiable for me.
- **Parameterized the metric.** `METRIC` is a variable, not a string buried in a `sort_values` call. Now the same script analyzes revenue, hours, signups — whatever column I pass.
- **Wrote results back.** Instead of printing to a terminal nobody reads, I append the LLM's bullets to a fresh "Analysis" tab in the same sheet with a timestamp. The output lands where the data already lives.
- **Made the model swappable.** `MODEL` is an env var too. llama3 for speed, a bigger local model when I want sharper reads. Same pipeline.

## Where it breaks

I'd rather tell you the failure modes than pretend there aren't any.

**Service-account security.** That JSON key is a password to your Sheets and Drive. Leak it and someone has your data. Scope it to one sheet, rotate it, never commit it.

**The LLM still hallucinates on thin data.** Give it 4 rows and it'll invent a "clear upward trend." Patterns need enough signal — I don't trust the bullets under ~20 source rows.

**Rate limits and latency.** The Sheets API caps reads per minute, and a local model on a laptop is not instant. Fine for a daily report, wrong tool for a live dashboard.

## Takeaway

The split is the lesson. **Code that's deterministic should stay deterministic** — sorting, summing, typing, slicing. The LLM gets handed clean, pre-computed truth and does the one thing it beats code at: spotting the story across the rows.

Build it the other way around — LLM does the math, code does the reasoning — and you get a confident liar. Build it this way and you get an analyst that doesn't make up numbers, because you never let it touch them.

*Built on and credited to Aman Kharwal's tutorial, ["Connect Your LLM to Google Sheets."](https://amanxai.com/2026/04/26/connect-your-llm-to-google-sheets/) I adapted the architecture and extended it with env-based secrets, a parameterized metric, write-back, and a swappable model.*

### Sources
- [Aman Kharwal — Connect Your LLM to Google Sheets](https://amanxai.com/2026/04/26/connect-your-llm-to-google-sheets/)
- [Google Cloud — AI Agent Trends 2026](https://cloud.google.com/resources/content/ai-agent-trends-2026)
