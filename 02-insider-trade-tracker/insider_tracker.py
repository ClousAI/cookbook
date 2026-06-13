#!/usr/bin/env python3
"""
Insider-trade tracker.

Pull recent Form 3/4/5 insider transactions for a ticker, classify each as a
buy / sell / grant / exercise, and flag *clusters* — multiple insiders trading
the same direction within a short window (a stronger signal than any single trade).

Endpoint: GET /v1/insider
  Useful filters: ticker, issuer_cik / owner_cik, trans_code, acquired_disposed,
  date_from / date_to, min_value_usd, derivative.

SEC transaction codes (trans_code):
  P = open-market purchase   S = open-market sale
  A = grant/award            M = option exercise
  F = shares withheld for tax   G = gift   D = disposition to issuer

Run:
    export CLOUS_API_KEY=clous_live_...
    python insider_tracker.py NVDA
"""
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402

# How we read each SEC transaction code.
BUY_CODES = {"P"}            # cash purchases on the open market
SELL_CODES = {"S"}           # cash sales on the open market
NEUTRAL = {"A", "M", "F", "G", "D"}  # grants/exercises/tax/gifts — not open-market conviction


def classify(row: dict) -> str:
    code = (row.get("trans_code") or "").upper()
    if code in BUY_CODES:
        return "BUY"
    if code in SELL_CODES:
        return "SELL"
    # Fall back to the acquired/disposed flag for anything else.
    ad = (row.get("acquired_disposed") or "").upper()
    if code in NEUTRAL:
        return f"{code}/{'acq' if ad == 'A' else 'disp'}"
    return code or "?"


def main() -> None:
    ticker = (sys.argv[1] if len(sys.argv) > 1 else "NVDA").upper()
    lookback_days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    date_from = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    print(f"Insider transactions for {ticker} since {date_from}\n")

    rows = list(
        clous.paginate(
            "/v1/insider",
            {"ticker": ticker, "date_from": date_from, "limit": 100},
            max_items=500,
        )
    )
    if not rows:
        print("No transactions found in the window.")
        return

    # --- Print and tally -------------------------------------------------
    by_owner_buy = defaultdict(list)
    by_owner_sell = defaultdict(list)
    for r in rows:
        kind = classify(r)
        value = r.get("value_usd") or 0
        print(
            f"  {r.get('trans_date'):<11} {kind:<10} "
            f"{(r.get('owner_name') or '')[:28]:<28} "
            f"{(r.get('owner_relationship') or '')[:18]:<18} "
            f"{r.get('shares', 0):>12,} sh  ${value:>14,.0f}"
        )
        if kind == "BUY":
            by_owner_buy[r.get("owner_name")].append(r)
        elif kind == "SELL":
            by_owner_sell[r.get("owner_name")].append(r)

    # --- Cluster flag ----------------------------------------------------
    # A "cluster" = 3+ distinct insiders trading the same direction in the window.
    print("\n--- Cluster analysis (open-market P/S only) ---")
    buyers = [o for o in by_owner_buy if o]
    sellers = [o for o in by_owner_sell if o]
    buy_value = sum(r.get("value_usd") or 0 for rs in by_owner_buy.values() for r in rs)
    sell_value = sum(r.get("value_usd") or 0 for rs in by_owner_sell.values() for r in rs)

    print(f"  open-market BUYERS : {len(buyers):>2}  (${buy_value:,.0f})")
    print(f"  open-market SELLERS: {len(sellers):>2}  (${sell_value:,.0f})")

    if len(buyers) >= 3:
        print(f"  🟢 BUY CLUSTER — {len(buyers)} insiders bought: {', '.join(buyers)}")
    if len(sellers) >= 3:
        print(f"  🔴 SELL CLUSTER — {len(sellers)} insiders sold: {', '.join(sellers)}")
    if len(buyers) < 3 and len(sellers) < 3:
        print("  No cluster (fewer than 3 insiders on either side).")


if __name__ == "__main__":
    main()
