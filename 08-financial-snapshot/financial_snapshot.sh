#!/usr/bin/env bash
# Company financial snapshot in curl + jq, using ?fields= for token-efficient payloads.
#
#   export CLOUS_API_KEY=clous_live_...
#   ./financial_snapshot.sh 320193        # Apple
set -euo pipefail
source "$(dirname "$0")/../_shared/clous.sh"

CIK="${1:-320193}"
FIELDS="concept,label,value,unit,fiscal_year,fiscal_period,period_end,form,filed"

echo "Financial snapshot for CIK ${CIK}"
echo

# Pull a few key concepts; for each, show the most recently filed value.
for CONCEPT in \
  "us-gaap:Revenues" \
  "us-gaap:NetIncomeLoss" \
  "us-gaap:Assets" \
  "us-gaap:StockholdersEquity" \
  "us-gaap:EarningsPerShareDiluted" \
  "us-gaap:CashAndCashEquivalentsAtCarryingValue"
do
  ENC=$(printf %s "$CONCEPT" | jq -sRr @uri)
  clous_get "/v1/financials/${CIK}?concept=${ENC}&fields=${FIELDS}" | jq -r '
    (.data | sort_by(.filed, .period_end) | last) as $f |
    if $f == null then empty
    else "  \($f.label // $f.concept)  =  \($f.value) \($f.unit // "")  (\($f.fiscal_year)\(if $f.fiscal_period then "-" + $f.fiscal_period else "" end), \($f.form), filed \($f.filed))"
    end'
done

echo
echo "Note the ?fields= param: it trims each row to the columns you name — smaller"
echo "responses and far fewer tokens when feeding the result into an LLM."
