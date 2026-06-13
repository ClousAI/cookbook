#!/usr/bin/env python3
"""
Company financial snapshot.

Pull a company's XBRL facts from GET /v1/financials/{cik}, pick out the key
metrics (revenue, net income, assets, EPS, shares), and show the latest reported
value for each. Demonstrates `?fields=` projection to slash response size — handy
when you're feeding results to an LLM and paying per token.

Endpoint: GET /v1/financials/{cik}
  Optional `concept` filters to one XBRL concept (e.g. us-gaap:Revenues).
  Each fact: { concept, label, unit, value, fiscal_year, fiscal_period,
               period_start, period_end, form, filed, accession }

Run:
    export CLOUS_API_KEY=clous_live_...
    python financial_snapshot.py 320193        # Apple
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402

# The XBRL concepts we want for a quick snapshot, in display order.
KEY_CONCEPTS = [
    ("us-gaap:Revenues", "Revenue"),
    ("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "Revenue (ASC 606)"),
    ("us-gaap:NetIncomeLoss", "Net income"),
    ("us-gaap:Assets", "Total assets"),
    ("us-gaap:Liabilities", "Total liabilities"),
    ("us-gaap:StockholdersEquity", "Stockholders' equity"),
    ("us-gaap:EarningsPerShareDiluted", "EPS (diluted)"),
    ("us-gaap:CashAndCashEquivalentsAtCarryingValue", "Cash & equivalents"),
]


def latest(facts):
    """Pick the most recently *filed* fact (then latest period_end)."""
    return max(facts, key=lambda f: (f.get("filed") or "", f.get("period_end") or ""))


def fmt(value, unit):
    if value is None:
        return "n/a"
    if unit in (None, "USD", "shares"):
        return f"{value:,.0f}" + (f" {unit}" if unit == "shares" else "")
    return f"{value:,.2f} {unit}"


def main() -> None:
    cik = sys.argv[1] if len(sys.argv) > 1 else "320193"
    print(f"Financial snapshot for CIK {cik}\n")

    # --- Token efficiency: project only the fields we render with ?fields= -----
    # The full company-facts response can be tens of thousands of rows; asking for
    # just these columns keeps payloads (and LLM token bills) small.
    fields = "concept,label,value,unit,fiscal_year,fiscal_period,period_end,form,filed"

    # One efficient strategy: fetch per-concept so each call is tiny.
    print(f"{'Metric':<22} {'Value':>22}  {'Period':<10} {'Form':<6} {'Filed'}")
    print("-" * 80)
    seen_name = None
    for concept, label in KEY_CONCEPTS:
        env = clous.get(f"/v1/financials/{cik}", {"concept": concept, "fields": fields})
        seen_name = seen_name or (env.get("query_echo") or {}).get("entity_name")
        facts = env.get("data") or []
        if not facts:
            continue
        f = latest(facts)
        period = f"{f.get('fiscal_year')}{('-' + f['fiscal_period']) if f.get('fiscal_period') else ''}"
        print(f"{label:<22} {fmt(f.get('value'), f.get('unit')):>22}  "
              f"{period:<10} {f.get('form', ''):<6} {f.get('filed', '')}")

    if seen_name:
        print(f"\nentity: {seen_name}")
    print("\nTip: `?fields=` returns only the columns you name — smaller payloads,")
    print("fewer tokens when piping into an LLM. `?output_schema=` can rename/reshape.")


if __name__ == "__main__":
    main()
