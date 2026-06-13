# 03 · 13F change detector

Quarter-over-quarter position changes for a 13F institutional manager:
**new buys, exits, increases, trims**.

## What it does

- Pulls a manager's holdings via `GET /v1/holdings?manager=...`.
- Groups positions by reporting `period` (e.g. `31-DEC-2025`), picks the two most
  recent, and diffs them by `cusip`:
  - in current but not prior → **new position**
  - in prior but not current → **exit**
  - shares up / down → **increase** / **trim** (with % change)

## Run

```bash
export CLOUS_API_KEY=clous_live_...

python thirteenf_changes.py "Berkshire"
python thirteenf_changes.py "VANGUARD"

./thirteenf_changes.sh Berkshire        # curl + jq variant
```

## Notes

- A holding is keyed by **(manager, security/CUSIP, period)**, so a stock held
  across quarters appears once per quarter — exactly what we diff.
- Want it from the stock's side instead of the manager's? Query
  `GET /v1/holdings?cusip=037833100` (Apple) or `?issuer=APPLE` to see *every*
  manager's position and how it moved.
- The Python version paginates the manager's full book; the bash version reads
  one page (up to 100). For very large managers, follow `page.next_cursor`.

Endpoint reference: [docs.clous.ai/api/holdings](https://docs.clous.ai/api/holdings).
