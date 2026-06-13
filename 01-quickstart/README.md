# 01 · Quickstart

Your first authenticated Clous call, the response envelope, and cursor pagination.

## What it does

1. Sends one authenticated `GET /v1/filings` for a company (Apple, CIK `0000320193`).
2. Reads the **envelope** every endpoint returns:
   `data[]`, `page{limit, next_cursor, has_more}`, `as_of`, `source`,
   `query_echo`, `warnings`.
3. Walks a larger result set by following `page.next_cursor`.

## Run

```bash
export CLOUS_API_KEY=clous_live_...

# Python
python quickstart.py

# curl + jq
./quickstart.sh
```

## Key ideas

- **Auth** is a single header: `Authorization: Bearer $CLOUS_API_KEY`.
- **Every** endpoint returns the same envelope, so you parse responses the same
  way across all of Clous.
- **Pagination is cursor-based.** Never compute offsets — pass the previous
  response's `page.next_cursor` as `?cursor=` and stop when `page.has_more` is
  `false`. The Python helper `clous.paginate()` does this loop for you.

Next: [02 · Insider-trade tracker](../02-insider-trade-tracker).
