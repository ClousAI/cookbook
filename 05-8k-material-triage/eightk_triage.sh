#!/usr/bin/env bash
# 8-K material-event triage in curl + jq.
# Lists recent 8-Ks for a CIK, then classifies each filing's items + materiality.
#
#   export CLOUS_API_KEY=clous_live_...
#   ./eightk_triage.sh 0000320193        # Apple
set -euo pipefail
source "$(dirname "$0")/../_shared/clous.sh"

CIK="${1:-0000320193}"
N="${2:-8}"

# Recent 8-K accessions for this company.
ACCS=$(clous_get "/v1/filings?cik=${CIK}&form_type=8-K&limit=${N}" | jq -r '.data[].accession')

echo "Triaging recent 8-Ks for CIK ${CIK}"
echo
for ACC in $ACCS; do
  # Classified numbered items (5.02 leadership, 1.05 cyber, etc.)
  ITEMS=$(clous_get "/v1/filings/${ACC}/events" \
    | jq -r '[(.data // .events // [])[] | (.item // .item_number // .number)] | join(", ")')
  # Rule-based materiality (1-3) + direction from the briefing endpoint.
  BRIEF=$(clous_get "/v1/filings/${ACC}/briefing" \
    | jq -r '(.data[0] // .) | "materiality=\(.materiality // "?") direction=\(.direction // "-")"')
  echo "  ${ACC}  items[${ITEMS:-—}]  ${BRIEF}"
done
echo
echo "High-signal items to watch: 1.01 agreement · 1.03 bankruptcy · 1.05 cyber ·"
echo "2.01 M&A · 3.01 delisting · 4.01/4.02 auditor/restatement · 5.01/5.02 control/leadership."
