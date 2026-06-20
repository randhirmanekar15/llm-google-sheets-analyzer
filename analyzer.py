"""Connect a local LLM to Google Sheets.

Hybrid design: deterministic Python does the math and sorting; the LLM only does
pattern recognition over a clean, pre-computed slice. The model never counts.

Inspired by Aman Kharwal's tutorial:
https://amanxai.com/2026/04/26/connect-your-llm-to-google-sheets/
"""

from __future__ import annotations

import os

import pandas as pd
import requests

MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
REQUEST_TIMEOUT = 120  # seconds


def clean_numeric(value: object) -> int:
    """Turn a formatted number like '1,250' into 1250; junk becomes 0."""
    try:
        return int(str(value).replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0


def load_sheet(sheet_id: str, creds_path: str) -> pd.DataFrame:
    """Authenticate with a service account and load a sheet as a DataFrame."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    records = client.open_by_key(sheet_id).sheet1.get_all_records()
    return pd.DataFrame(records)


def query_llm(prompt: str) -> str:
    """Send a prompt to the local Ollama model."""
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("response", "")


def analyze(df: pd.DataFrame, metric: str, top_n: int = 10) -> str:
    """Sort deterministically, then ask the LLM only to find patterns."""
    top = df.sort_values(by=metric, ascending=False).head(top_n)
    prompt = (
        f"You are a data analyst. Below are the top {top_n} rows by {metric}.\n"
        "Do NOT recalculate any numbers - trust them. Find patterns and trends. "
        "Max 5 bullets.\n\n"
        f"{top.to_string(index=False)}"
    )
    return query_llm(prompt)


def main() -> None:
    sheet_id = os.environ["SHEET_ID"]
    creds_path = os.environ["GSHEET_CREDS"]
    metric = os.environ.get("METRIC", "Hours Viewed")

    df = load_sheet(sheet_id, creds_path)
    if metric in df.columns:
        df[metric] = df[metric].apply(clean_numeric)
    print(analyze(df, metric))


if __name__ == "__main__":
    main()
