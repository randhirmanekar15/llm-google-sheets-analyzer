"""Tests for the deterministic helpers (no Google / model required)."""

import pandas as pd

import analyzer
from analyzer import analyze, clean_numeric


def test_clean_numeric_strips_commas():
    assert clean_numeric("1,250") == 1250


def test_clean_numeric_handles_junk():
    assert clean_numeric("n/a") == 0
    assert clean_numeric(None) == 0


def test_analyze_sorts_and_calls_llm(monkeypatch):
    captured = {}

    def fake_llm(prompt: str) -> str:
        captured["prompt"] = prompt
        return "ok"

    monkeypatch.setattr(analyzer, "query_llm", fake_llm)
    df = pd.DataFrame({"show": ["a", "b", "c"], "views": [10, 99, 50]})
    result = analyze(df, "views", top_n=2)
    assert result == "ok"
    # within the top-2 slice, the higher value must appear before the lower one
    assert captured["prompt"].index("99") < captured["prompt"].index("50")
