# 08 · Company financial snapshot

Turn a company's raw XBRL facts into a compact key-metrics snapshot, and use
`?fields=` to keep payloads (and LLM token bills) small.

## What it does

- Calls `GET /v1/financials/{cik}` — every XBRL-reported concept for one company,
  proxied live from SEC's company-facts data.
- Filters to a handful of key concepts (`us-gaap:Revenues`, `NetIncomeLoss`,
  `Assets`, `StockholdersEquity`, `EarningsPerShareDiluted`, cash) via `?concept=`.
- For each, picks the **most recently filed** fact and prints value + period + form.

## Token efficiency

The full company-facts response can be tens of thousands of rows. Two levers:

- **`?fields=concept,label,value,unit,fiscal_year,...`** — return only the columns
  you render. Smaller responses, fewer tokens downstream.
- **`?concept=us-gaap:Revenues`** — fetch one concept at a time so each call is tiny.
- **`?output_schema=`** — rename/reshape fields into exactly the structure your
  code or LLM expects.

These projection params work across Clous list endpoints, not just financials.

## Run

```bash
export CLOUS_API_KEY=clous_live_...

python financial_snapshot.py 320193       # Apple (CIK)
./financial_snapshot.sh 320193            # curl + jq variant
```

> Need a CIK? `GET /v1/entities?ticker=AAPL` resolves ticker → CIK.

Endpoint: [docs.clous.ai/api/financials-cik](https://docs.clous.ai/api/financials-cik).
