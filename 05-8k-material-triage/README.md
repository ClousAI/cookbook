# 05 · 8-K material-event triage

Recent 8-Ks are mostly noise. This recipe classifies each one by **numbered item**
and **materiality**, then surfaces the load-bearing reports.

## What it does

1. Lists recent 8-Ks for a company: `GET /v1/filings?cik=...&form_type=8-K`.
2. For each, classifies the reported items: `GET /v1/filings/{accession}/events`
   returns each numbered 8-K item (e.g. `5.02` leadership, `1.05` cyber) with its
   canonical title and an excerpt.
3. Pulls a **materiality score** (rule-based, 1–3) and **direction** from
   `GET /v1/filings/{accession}/briefing` — and, when a model is configured, a
   plain-English read.
4. Splits filings into **load-bearing** vs **routine** based on high-signal items
   (1.01, 1.03, 1.05, 2.01, 3.01, 4.01/4.02, 5.01/5.02) or materiality ≥ 2.

## Run

```bash
export CLOUS_API_KEY=clous_live_...

python eightk_triage.py 0000320193        # Apple, 10 filings
python eightk_triage.py 0001045810 8      # NVIDIA, 8 filings

./eightk_triage.sh 0000320193             # curl + jq variant
```

> Need the CIK for a ticker? `GET /v1/entities?ticker=NVDA` resolves it, or just
> use `GET /v1/filings?q=nvidia`.

## Related

- For a curated cross-company feed of **only** cyber incidents (Item 1.05), use
  `GET /v1/cyber-incidents`.
- To get pushed every new material 8-K, create a monitor on
  `sec.8k.executive_change` / `sec.8k.material_agreement` etc. — see
  [07 · Monitor + webhook](../07-monitor-webhook).
