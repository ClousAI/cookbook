#!/usr/bin/env python3
"""
Quickstart — your first authenticated Clous call.

Shows three things every Clous integration relies on:
  1. Authenticating with your Bearer key.
  2. Reading the standard response envelope (data / page / as_of / source / warnings).
  3. Cursor pagination — following page.next_cursor to walk a large result set.

Run:
    export CLOUS_API_KEY=clous_live_...
    python quickstart.py
"""
import os
import sys

# Make the shared helper importable without installing anything.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402


def main() -> None:
    # --- 1. One authenticated request -------------------------------------
    # /v1/filings is the EDGAR filing index. Grab the 5 most recent Apple filings.
    # CIK 0000320193 = Apple Inc.
    env = clous.get("/v1/filings", {"cik": "0000320193", "limit": 5})

    # --- 2. Read the envelope --------------------------------------------
    print(f"source   : {env['source']}")
    print(f"as_of    : {env.get('as_of')}")
    print(f"returned : {len(env['data'])} rows")
    print(f"page     : {env['page']}")
    if env.get("warnings"):
        print(f"warnings : {env['warnings']}")
    print()

    for f in env["data"]:
        # Filing records carry the form type, filing date, and accession number.
        print(f"  {f.get('filed_date') or f.get('filed'):<12} "
              f"{f.get('form_type', '?'):<8} {f.get('accession')}")

    # --- 3. Cursor pagination --------------------------------------------
    # Walk up to 30 Apple 8-K filings across pages. clous.paginate() follows
    # page.next_cursor for you until has_more is false (or the cap is hit).
    print("\nPaginating Apple 8-Ks (up to 30):")
    count = 0
    for filing in clous.paginate(
        "/v1/filings",
        {"cik": "0000320193", "form_type": "8-K", "limit": 10},
        max_items=30,
    ):
        count += 1
    print(f"  walked {count} filings across multiple pages")


if __name__ == "__main__":
    main()
