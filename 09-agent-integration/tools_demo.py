#!/usr/bin/env python3
"""
Tool-using agent — expose Clous REST endpoints as OpenAI-style function tools.

When you want YOUR model (any tool-calling LLM) to decide when to hit Clous, give
it function definitions that map to Clous endpoints, then execute the tool calls
against api.clous.ai. This file:

  - defines a couple of Clous tools in OpenAI `tools` JSON-Schema format
  - implements the executor that turns a tool call into a Clous REST request
  - runs a tiny manual loop you can drop into any agent framework

It runs WITHOUT an LLM by default (demonstrates the executor on a hard-coded tool
call), and includes commented code for the full OpenAI tool-calling loop.

Run:
    export CLOUS_API_KEY=clous_live_...
    python tools_demo.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402

# 1. Tool schemas — the shape any OpenAI-compatible tool-calling model expects.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_insider_transactions",
            "description": "Search SEC Form 3/4/5 insider trades by issuer ticker, "
                           "transaction code, and date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Issuer ticker, e.g. NVDA."},
                    "trans_code": {"type": "string", "description": "P=buy, S=sell, etc."},
                    "date_from": {"type": "string", "description": "YYYY-MM-DD."},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["ticker"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_financials",
            "description": "Structured XBRL financial facts for one company by CIK.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cik": {"type": "string"},
                    "concept": {"type": "string", "description": "e.g. us-gaap:Revenues."},
                },
                "required": ["cik"],
            },
        },
    },
]

# 2. Executor — map a tool name + args to a real Clous REST call.
def execute_tool(name: str, args: dict):
    if name == "search_insider_transactions":
        return clous.get("/v1/insider", {
            "ticker": args.get("ticker"),
            "trans_code": args.get("trans_code"),
            "date_from": args.get("date_from"),
            "limit": args.get("limit", 10),
        })
    if name == "get_company_financials":
        cik = args["cik"]
        return clous.get(f"/v1/financials/{cik}", {"concept": args.get("concept")})
    raise ValueError(f"unknown tool: {name}")


def main() -> None:
    # --- Demo: run the executor directly on a sample tool call --------------
    sample_call = {"name": "search_insider_transactions",
                   "arguments": {"ticker": "NVDA", "trans_code": "S", "limit": 5}}
    print(f"Executing tool: {sample_call['name']}({sample_call['arguments']})\n")
    result = execute_tool(sample_call["name"], sample_call["arguments"])
    for row in result.get("data", [])[:5]:
        print(f"  {row.get('trans_date')}  {row.get('owner_name')}  "
              f"{row.get('shares')} sh  ${row.get('value_usd', 0):,.0f}")

    # --- Full LLM tool-calling loop (uncomment; pip install openai) ---------
    #
    #   from openai import OpenAI
    #   client = OpenAI()  # your own LLM provider/key
    #   messages = [{"role": "user", "content": "Any insider selling at NVDA lately?"}]
    #   resp = client.chat.completions.create(
    #       model="gpt-4o", messages=messages, tools=TOOLS)
    #   choice = resp.choices[0].message
    #   for tc in (choice.tool_calls or []):
    #       out = execute_tool(tc.function.name, json.loads(tc.function.arguments))
    #       messages.append(choice)
    #       messages.append({"role": "tool", "tool_call_id": tc.id,
    #                        "content": json.dumps(out)[:6000]})
    #   final = client.chat.completions.create(model="gpt-4o", messages=messages)
    #   print(final.choices[0].message.content)


if __name__ == "__main__":
    main()
