#!/usr/bin/env python3
"""
IPO / Form D monitor.

Two complementary capital-formation signals in one place:

  1. New S-1 registrations (companies filing to go public) — via GET /v1/filings
     filtered to form_type=S-1.
  2. Form D private placements (private capital raises) — via GET /v1/raises,
     filterable by sector/industry, state, fund type, and minimum amount.

Run:
    export CLOUS_API_KEY=clous_live_...
    python ipo_formd_monitor.py                 # defaults: last 30d S-1s + CA venture raises
    python ipo_formd_monitor.py 14 "Technology" # lookback days + industry substring
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402


def recent_s1_registrations(date_from: str, limit: int = 25):
    """New S-1 IPO registration filings since date_from, newest first."""
    print(f"=== New S-1 registrations since {date_from} ===")
    rows = list(
        clous.paginate(
            "/v1/filings",
            {"form_type": "S-1", "filed_from": date_from, "limit": 50},
            max_items=limit,
        )
    )
    if not rows:
        print("  (none)")
    for f in rows:
        name = f.get("company_name") or f.get("entity_name") or f.get("name") or "?"
        filed = f.get("filed_date") or f.get("filed")
        print(f"  {filed:<12} {name[:48]:<48} {f.get('accession')}")
    print()


def recent_form_d_raises(industry: Optional[str], state: Optional[str], min_amount: int):
    """Recent Form D private placements, optionally scoped to a sector/state."""
    scope = []
    if industry:
        scope.append(f"industry~{industry}")
    if state:
        scope.append(f"state={state}")
    scope.append(f"min ${min_amount:,}")
    print(f"=== Form D raises ({', '.join(scope)}) ===")

    rows = list(
        clous.paginate(
            "/v1/raises",
            {
                "industry": industry,
                "state": state,
                "min_amount": min_amount,
                "limit": 50,
            },
            max_items=25,
        )
    )
    if not rows:
        print("  (none)")
    for r in rows:
        offered = r.get("total_offering_amount") or 0
        sold = r.get("total_amount_sold") or 0
        print(
            f"  {r.get('filed_at'):<12} {(r.get('issuer_name') or '')[:38]:<38} "
            f"{(r.get('investment_fund_type') or r.get('industry_group') or '')[:22]:<22} "
            f"offered ${offered:>14,.0f}  sold ${sold:>14,.0f}"
        )
    print()


def main() -> None:
    lookback_days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    industry = sys.argv[2] if len(sys.argv) > 2 else None
    date_from = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    recent_s1_registrations(date_from)
    # Default sector demo: California venture raises >= $1M if no industry passed.
    recent_form_d_raises(
        industry=industry,
        state=None if industry else "CA",
        min_amount=1_000_000,
    )


if __name__ == "__main__":
    main()
