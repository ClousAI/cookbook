#!/usr/bin/env python3
"""
Agent integration — wire Clous into an LLM agent.

The simplest path: treat Clous's OpenAI-compatible endpoint as the model itself.
Point any OpenAI client at base_url=https://api.clous.ai/v1, model="clous", and
every answer is grounded in SEC filings with citations attached under `clous`.

This script shows that with a plain `requests` call (no extra dependency) and,
in a comment, the one-liner with the official `openai` package.

For a *tool-using* agent (your own model decides when to call Clous), see
tools_demo.py, which wraps Clous REST endpoints as OpenAI-style tool/function
definitions you can hand to any tool-calling LLM.

Run:
    export CLOUS_API_KEY=clous_live_...
    python agent.py "Compare NVDA and AMD data-center revenue growth last quarter."
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402


def ask(question: str) -> None:
    resp = clous.post(
        "/v1/chat/completions",
        {
            "model": "clous",
            "messages": [
                {"role": "system", "content": "You are a precise SEC-filings analyst."},
                {"role": "user", "content": question},
            ],
        },
    )
    msg = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
    print(msg or json.dumps(resp)[:1000])
    if resp.get("clous"):
        print("\n--- citations / basis (under `clous`) ---")
        print(json.dumps(resp["clous"], indent=2)[:800])


# Equivalent with the official OpenAI SDK (pip install openai):
#
#   from openai import OpenAI
#   client = OpenAI(base_url="https://api.clous.ai/v1",
#                   api_key=os.environ["CLOUS_API_KEY"])
#   resp = client.chat.completions.create(
#       model="clous",
#       messages=[{"role": "user", "content": question}],
#   )
#   print(resp.choices[0].message.content)


def main() -> None:
    q = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What were Apple's biggest disclosed risk factors in its latest 10-K?"
    )
    ask(q)


if __name__ == "__main__":
    main()
