# 09 · Agent integration

Three ways to put Clous inside an LLM agent — pick by how much control you want.

## A. Clous *as the model* (OpenAI-compatible) — `agent.py`

The least code. Point any OpenAI client at `base_url=https://api.clous.ai/v1`,
`model="clous"`, and every answer is grounded in SEC filings with citations under
a `clous` key.

```python
from openai import OpenAI
client = OpenAI(base_url="https://api.clous.ai/v1", api_key="clous_live_...")
resp = client.chat.completions.create(
    model="clous",
    messages=[{"role": "user", "content": "Apple's biggest 10-K risk factors?"}],
)
print(resp.choices[0].message.content)
```

`agent.py` does the same with plain `requests` (no extra dependency).

## B. Clous *as tools* for your own model — `tools_demo.py`

When your own LLM should decide *when* to query Clous, expose Clous endpoints as
OpenAI-style function tools. `tools_demo.py` ships:

- tool schemas (`search_insider_transactions`, `get_company_financials`) in
  OpenAI `tools` JSON-Schema format,
- an **executor** that turns a tool call into a real Clous REST request,
- a runnable demo (no LLM required) plus the commented full tool-calling loop.

## C. Clous over MCP — `mcp.config.json`

The Clous **[MCP server](https://www.npmjs.com/package/@clous/mcp)** exposes
filings, financials, insider trades, 13F, Form D, full-text search, and more as
MCP tools — for Claude Desktop, Cursor, or any MCP client. No code; just config:

```json
{
  "mcpServers": {
    "clous": {
      "command": "npx",
      "args": ["-y", "@clous/mcp"],
      "env": { "CLOUS_API_KEY": "clous_live_..." }
    }
  }
}
```

Claude Desktop: Settings → Developer → Edit Config. Cursor: `.cursor/mcp.json`.

## Run

```bash
export CLOUS_API_KEY=clous_live_...

python agent.py "Compare NVDA and AMD data-center revenue growth last quarter."
python tools_demo.py
```

## Which to use

| You want… | Use |
| --- | --- |
| Quick grounded answers, no orchestration | **A** — `model="clous"` |
| Your model to mix Clous with other tools/data | **B** — tool schemas + executor |
| A desktop/IDE agent (Claude Desktop, Cursor) | **C** — MCP server |
