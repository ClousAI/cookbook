#!/usr/bin/env python3
"""
8-K material-event triage.

Recent 8-K current reports are noisy — most are routine (earnings press releases,
Reg FD housekeeping). This recipe pulls recent 8-Ks for a company, classifies the
numbered items each one reports, scores materiality, and surfaces the
load-bearing ones (leadership changes, M&A, bankruptcy, delisting, cyber).

Endpoints:
  GET /v1/filings?form_type=8-K&cik=...           list recent 8-Ks
  GET /v1/filings/{accession}/events              classify the 8-K's numbered items
  GET /v1/filings/{accession}/briefing            rule-based materiality (1-3) + direction,
                                                  plus a plain-English read when a model is configured

Run:
    export CLOUS_API_KEY=clous_live_...
    python eightk_triage.py 0000320193        # Apple's CIK
    python eightk_triage.py 0001045810 8       # NVIDIA, look at 8 filings
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402

# 8-K items we consider load-bearing (material), by SEC item number.
HIGH_SIGNAL_ITEMS = {
    "1.01": "Material definitive agreement",
    "1.03": "Bankruptcy or receivership",
    "1.05": "Material cybersecurity incident",
    "2.01": "Completion of acquisition/disposition",
    "3.01": "Delisting / listing-standard notice",
    "4.01": "Auditor change",
    "4.02": "Non-reliance on prior financials (restatement)",
    "5.01": "Change in control",
    "5.02": "Departure/appointment of directors or officers",
}


def item_numbers(events_resp: dict):
    """Extract the list of 8-K item numbers from the /events response."""
    data = events_resp.get("data") or events_resp.get("events") or []
    items = []
    for ev in data:
        # The endpoint returns each reported item with its number, title, excerpt.
        num = ev.get("item") or ev.get("item_number") or ev.get("number")
        title = ev.get("title") or ev.get("item_title")
        if num:
            items.append((str(num), title))
    return items


def main() -> None:
    cik = sys.argv[1] if len(sys.argv) > 1 else "0000320193"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    print(f"Triaging the {n} most recent 8-Ks for CIK {cik}\n")
    filings = list(
        clous.paginate(
            "/v1/filings",
            {"cik": cik, "form_type": "8-K", "limit": 25},
            max_items=n,
        )
    )
    if not filings:
        print("No 8-K filings found.")
        return

    material, routine = [], []
    for f in filings:
        acc = f.get("accession")
        filed = f.get("filed_date") or f.get("filed")

        # 1. Classify the items this 8-K reports.
        try:
            ev = clous.get(f"/v1/filings/{acc}/events")
            items = item_numbers(ev)
        except SystemExit:
            items = []

        # 2. Pull the rule-based materiality score (1-3) from the briefing.
        materiality = None
        direction = None
        try:
            brief = clous.get(f"/v1/filings/{acc}/briefing")
            bd = (brief.get("data") or [brief])[0] if isinstance(brief.get("data"), list) else brief
            materiality = bd.get("materiality") or brief.get("materiality")
            direction = bd.get("direction") or brief.get("direction")
        except SystemExit:
            pass

        hits = [(num, HIGH_SIGNAL_ITEMS[num]) for num, _ in items if num in HIGH_SIGNAL_ITEMS]
        record = (acc, filed, items, hits, materiality, direction)
        (material if hits or (materiality and materiality >= 2) else routine).append(record)

    def show(rec):
        acc, filed, items, hits, materiality, direction = rec
        item_str = ", ".join(num for num, _ in items) or "—"
        m = f"materiality={materiality}" if materiality is not None else "materiality=?"
        d = f" direction={direction}" if direction else ""
        print(f"  {filed:<12} {acc}  items[{item_str}]  {m}{d}")
        for num, label in hits:
            print(f"       ⚠️  Item {num}: {label}")

    print("=== LOAD-BEARING 8-Ks ===")
    if not material:
        print("  (none in this window)")
    for rec in material:
        show(rec)

    print("\n=== Routine ===")
    for rec in routine:
        show(rec)


if __name__ == "__main__":
    main()
