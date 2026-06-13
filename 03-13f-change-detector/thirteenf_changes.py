#!/usr/bin/env python3
"""
13F change detector.

Compare a 13F manager's reported positions across the two most recent quarters
and surface what changed: new buys, exits, adds, and trims — quarter over quarter.

Endpoint: GET /v1/holdings
  Each record is one manager's position in one security for one reporting period:
  { manager_name, period, issuer, cusip, value_usd, shares, shares_type,
    investment_discretion, accession }
  Filters: manager (substring), issuer (substring), cusip, min_value.

Run:
    export CLOUS_API_KEY=clous_live_...
    python thirteenf_changes.py "Berkshire"
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402


def parse_period(p: str):
    """13F periods look like '31-DEC-2025'. Sort key = (year, month). Best-effort."""
    months = {m: i for i, m in enumerate(
        ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
         "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], start=1)}
    try:
        day, mon, year = p.split("-")
        return (int(year), months.get(mon.upper(), 0))
    except Exception:
        return (0, 0)


def main() -> None:
    manager = sys.argv[1] if len(sys.argv) > 1 else "Berkshire"
    print(f"13F position changes for manager matching: {manager!r}\n")

    # Pull a generous slice of this manager's holdings across periods.
    rows = list(
        clous.paginate("/v1/holdings", {"manager": manager, "limit": 100}, max_items=4000)
    )
    if not rows:
        print("No holdings found for that manager.")
        return

    # Group positions by reporting period.
    by_period = defaultdict(dict)  # period -> {cusip: row}
    for r in rows:
        period = r.get("period")
        cusip = r.get("cusip")
        if period and cusip:
            by_period[period][cusip] = r

    periods = sorted(by_period.keys(), key=parse_period, reverse=True)
    if len(periods) < 2:
        print(f"Only one reporting period available ({periods}). Need two to diff.")
        return

    curr_p, prev_p = periods[0], periods[1]
    curr, prev = by_period[curr_p], by_period[prev_p]
    name = rows[0].get("manager_name", manager)
    print(f"Manager : {name}")
    print(f"Compare : {prev_p}  ->  {curr_p}\n")

    new_buys, exits, adds, trims = [], [], [], []
    for cusip, row in curr.items():
        issuer = row.get("issuer", cusip)
        cur_sh = row.get("shares") or 0
        if cusip not in prev:
            new_buys.append((issuer, cur_sh, row.get("value_usd") or 0))
        else:
            prev_sh = prev[cusip].get("shares") or 0
            if cur_sh > prev_sh:
                adds.append((issuer, prev_sh, cur_sh))
            elif cur_sh < prev_sh:
                trims.append((issuer, prev_sh, cur_sh))
    for cusip, row in prev.items():
        if cusip not in curr:
            exits.append((row.get("issuer", cusip), row.get("shares") or 0))

    def pct(old, new):
        return "n/a" if not old else f"{(new - old) / old * 100:+.0f}%"

    print(f"🆕 NEW POSITIONS ({len(new_buys)}):")
    for issuer, sh, val in sorted(new_buys, key=lambda x: -x[2])[:15]:
        print(f"   {issuer[:40]:<40} {sh:>14,} sh  ${val:>15,.0f}")

    print(f"\n❌ EXITED ({len(exits)}):")
    for issuer, sh in sorted(exits, key=lambda x: -x[1])[:15]:
        print(f"   {issuer[:40]:<40} was {sh:>14,} sh")

    print(f"\n⬆️  INCREASED ({len(adds)}):")
    for issuer, o, n in sorted(adds, key=lambda x: -(x[2] - x[1]))[:15]:
        print(f"   {issuer[:40]:<40} {o:>12,} -> {n:>12,} sh  ({pct(o, n)})")

    print(f"\n⬇️  TRIMMED ({len(trims)}):")
    for issuer, o, n in sorted(trims, key=lambda x: (x[2] - x[1]))[:15]:
        print(f"   {issuer[:40]:<40} {o:>12,} -> {n:>12,} sh  ({pct(o, n)})")


if __name__ == "__main__":
    main()
