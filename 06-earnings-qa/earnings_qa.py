#!/usr/bin/env python3
"""
Earnings Q&A — grounded, cited answers over SEC filings.

Two ways to ask Clous a natural-language question about filings:

  A) POST /v1/answer          — purpose-built: returns an answer synthesized
                                strictly from filing text, with citations and a
                                basis (confidence + reasoning). Scope with
                                ticker / cik / accession / forms; cap sources with
                                max_sources (1-8). Pass output_schema (JSON Schema)
                                for a structured answer.

  B) POST /v1/chat/completions — OpenAI-compatible. Point any OpenAI client at
                                base_url=https://api.clous.ai/v1, model="clous".
                                Citations + basis ride along under `clous`.

Run:
    export CLOUS_API_KEY=clous_live_...
    python earnings_qa.py NVDA "How did data center revenue trend last quarter?"
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402


def grounded_answer(ticker: str, question: str) -> None:
    """A) The dedicated /v1/answer endpoint — best for cited, scoped Q&A."""
    print("=== /v1/answer (grounded + cited) ===")
    resp = clous.post(
        "/v1/answer",
        {
            "q": question,
            "ticker": ticker,         # scope to one entity; or pass cik / accession
            "forms": "10-Q,10-K,8-K",  # restrict to the filings that matter for earnings
            "max_sources": 6,          # 1-8
        },
    )
    print("Q:", question, "\n")
    print("A:", resp.get("answer") or resp.get("text") or json.dumps(resp)[:800])
    basis = resp.get("basis") or {}
    if basis:
        print("\nBasis:", json.dumps(basis, indent=2)[:600])
    cites = resp.get("citations") or resp.get("sources") or []
    if cites:
        print("\nCitations:")
        for c in cites:
            label = c.get("accession") or c.get("url") or c.get("title") or c
            print(f"  - {label}")


def structured_answer(ticker: str) -> None:
    """A') Same endpoint, but ask for a typed result via output_schema."""
    print("\n=== /v1/answer with output_schema (structured) ===")
    schema = {
        "type": "object",
        "properties": {
            "metric": {"type": "string"},
            "value": {"type": "string"},
            "period": {"type": "string"},
            "yoy_change": {"type": "string"},
        },
        "required": ["metric", "value"],
    }
    resp = clous.post(
        "/v1/answer",
        {
            "q": "What was total revenue most recent reported quarter, and the YoY change?",
            "ticker": ticker,
            "forms": "10-Q,10-K",
            "output_schema": schema,
        },
    )
    print(json.dumps(resp.get("answer") or resp, indent=2)[:800])


def openai_compatible(question: str) -> None:
    """
    B) OpenAI-compatible endpoint. Shown with a plain requests call so there's no
    extra dependency; the equivalent with the `openai` package is in the README.
    """
    print("\n=== /v1/chat/completions (OpenAI-compatible) ===")
    resp = clous.post(
        "/v1/chat/completions",
        {
            "model": "clous",
            "messages": [
                {"role": "user", "content": question},
            ],
        },
    )
    choices = resp.get("choices") or []
    if choices:
        print(choices[0].get("message", {}).get("content", "")[:800])
    # Clous attaches citations/basis under a `clous` key on the response.
    if resp.get("clous"):
        print("\nclous:", json.dumps(resp["clous"], indent=2)[:500])


def main() -> None:
    ticker = (sys.argv[1] if len(sys.argv) > 1 else "NVDA").upper()
    question = (
        sys.argv[2]
        if len(sys.argv) > 2
        else f"Summarize {ticker}'s most recent quarterly results and key risks."
    )

    grounded_answer(ticker, question)
    structured_answer(ticker)
    openai_compatible(f"For {ticker}: {question}")


if __name__ == "__main__":
    main()
