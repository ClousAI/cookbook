# Clous Cookbook

Runnable, copy-pasteable recipes for the **[Clous](https://clous.ai) SEC/EDGAR API** —
the fastest path from *curious* to *integrated*.

Clous turns raw SEC EDGAR filings into one consistent, entity-resolved JSON API:
filings, insider trades (Form 3/4/5), 13D/G ownership, 13F holdings, Form ADV
advisers, Form D raises, XBRL financials, full-text search, a normalized
**events feed**, **monitors + signed webhooks**, and a grounded, cited **AI answer**
endpoint (plus an OpenAI-compatible `/v1/chat/completions`).

Every recipe is self-contained, reads your key from `$CLOUS_API_KEY`, and ships in
**both Python and curl/bash** where it makes sense.

---

## Prerequisites

1. **Get an API key** — sign up at [clous.ai](https://clous.ai). Keys look like
   `clous_live_...`.
2. **Export it:**

   ```bash
   # macOS / Linux
   export CLOUS_API_KEY=clous_live_...
   ```
   ```powershell
   # Windows PowerShell
   $env:CLOUS_API_KEY="clous_live_..."
   ```
3. **Python recipes:** Python 3.9+ and

   ```bash
   pip install -r requirements.txt
   ```
4. **curl recipes:** `curl` and [`jq`](https://jqlang.github.io/jq/) for JSON parsing.

> Don't have a key yet? Read the scripts anyway — they're short and document the
> exact endpoints, params, and response shapes.

---

## API in 30 seconds

- **Base URL:** `https://api.clous.ai` · **Auth:** `Authorization: Bearer $CLOUS_API_KEY`
- **One envelope for everything:**

  ```json
  {
    "data": [ ... ],
    "page": { "limit": 25, "next_cursor": "…", "has_more": true },
    "as_of": "2026-06-13T00:00:00Z",
    "source": "insider",
    "query_echo": { "ticker": "AAPL" },
    "warnings": []
  }
  ```
- **Pagination:** cursor-based — pass the previous page's `page.next_cursor` as `?cursor=`.
- **Token efficiency:** ask for fewer fields with `?fields=col1,col2` or reshape with
  `?output_schema=` (a JSON object mapping output keys to source fields).
- **AI:** `POST /v1/answer` (grounded + cited) and an OpenAI-compatible
  `POST /v1/chat/completions` (model `clous`).
- **MCP:** an MCP server ships as [`@clousai/mcp`](https://www.npmjs.com/package/@clousai/mcp)
  for agent/tool use — see recipe 09.

Full reference lives at **[docs.clous.ai](https://docs.clous.ai)**.

---

## Recipes

| # | Recipe | What you learn | Languages |
| --- | --- | --- | --- |
| 01 | [Quickstart](./01-quickstart) | First authenticated call, reading the envelope, cursor pagination | Python · curl |
| 02 | [Insider-trade tracker](./02-insider-trade-tracker) | Pull recent Form 4s for a ticker, classify buy/sell, flag clusters | Python · curl |
| 03 | [13F change detector](./03-13f-change-detector) | Quarter-over-quarter position changes for a manager / stock | Python · curl |
| 04 | [IPO / Form D monitor](./04-ipo-formd-monitor) | New S-1 registrations + Form D private placements in a sector | Python · curl |
| 05 | [8-K material-event triage](./05-8k-material-triage) | Classify recent 8-Ks by item + materiality, surface load-bearing ones | Python · curl |
| 06 | [Earnings Q&A](./06-earnings-qa) | Grounded, cited `/v1/answer` + OpenAI-compatible `/v1/chat/completions` | Python · curl |
| 07 | [Monitor + webhook](./07-monitor-webhook) | Create a monitor, register a webhook, verify the HMAC signature | Python · curl |
| 08 | [Company financial snapshot](./08-financial-snapshot) | `/v1/financials/{cik}` → key metrics, `?fields=` for token efficiency | Python · curl |
| 09 | [Agent integration](./09-agent-integration) | Wire Clous into an LLM agent via the OpenAI endpoint and/or MCP | Python |

Each folder has its own `README.md` and runnable script(s).

---

## Layout

```
clous-cookbook/
├── README.md                 # you are here
├── LICENSE                   # MIT
├── requirements.txt          # requests (+ optional extras)
├── _shared/
│   ├── clous.py              # tiny Python client: envelope unwrap + cursor pagination
│   └── clous.sh              # bash helpers: clous_get / clous_post
├── 01-quickstart/
├── 02-insider-trade-tracker/
├── 03-13f-change-detector/
├── 04-ipo-formd-monitor/
├── 05-8k-material-triage/
├── 06-earnings-qa/
├── 07-monitor-webhook/
├── 08-financial-snapshot/
└── 09-agent-integration/
```

The Python recipes import `_shared/clous.py` (they add the folder to `sys.path`),
so you can read each script top-to-bottom without jumping around. To use the
helper in your own project, just copy `_shared/clous.py` next to your code.

---

## License

MIT — see [LICENSE](./LICENSE). Data derives from public **SEC EDGAR** filings;
Clous is independent of the SEC.
