# 02 · Insider-trade tracker

Pull recent **Form 3/4/5** insider transactions for a ticker, classify each
trade, and flag **clusters** of insiders trading the same direction.

## What it does

- Queries `GET /v1/insider?ticker=...&date_from=...` and paginates the window.
- Classifies each row by SEC `trans_code`:
  - `P` → **BUY** (open-market purchase), `S` → **SELL** (open-market sale)
  - `A` grant, `M` exercise, `F` tax-withholding, `G` gift, `D` disposition —
    shown but treated as *neutral* (no cash conviction).
- Flags a **cluster** when 3+ distinct insiders bought (or sold) on the open
  market in the lookback window — a stronger signal than any single trade.

> Why ignore A/M/F? Awards and exercises usually have `price_per_share = 0` and
> `value_usd = 0` (no cash changes hands). To isolate conviction trades, filter
> `trans_code=P` (buys) or `trans_code=S` (sells), optionally with `min_value_usd`.

## Run

```bash
export CLOUS_API_KEY=clous_live_...

python insider_tracker.py NVDA          # ticker, default 90-day lookback
python insider_tracker.py AAPL 30       # ticker + custom lookback days

./insider_tracker.sh NVDA               # curl + jq variant
```

## Endpoint

`GET /v1/insider` — filters used here: `ticker`, `date_from`, `trans_code`.
Other useful ones: `issuer_cik` / `owner_cik` (fastest by `issuer_cik`),
`min_value_usd`, `acquired_disposed`, `derivative`. See
[docs.clous.ai/api/insider](https://docs.clous.ai/api/insider).
