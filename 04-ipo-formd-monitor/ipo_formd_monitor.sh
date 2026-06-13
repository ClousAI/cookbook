#!/usr/bin/env bash
# IPO / Form D monitor in curl + jq.
#
#   export CLOUS_API_KEY=clous_live_...
#   ./ipo_formd_monitor.sh                 # last 30d S-1s + CA venture raises
#   ./ipo_formd_monitor.sh 14 Technology   # lookback days + industry substring
set -euo pipefail
source "$(dirname "$0")/../_shared/clous.sh"

DAYS="${1:-30}"
INDUSTRY="${2:-}"
DATE_FROM=$(date -u -d "${DAYS} days ago" +%Y-%m-%d 2>/dev/null || date -u -v-"${DAYS}"d +%Y-%m-%d)

echo "=== New S-1 registrations since ${DATE_FROM} ==="
clous_get "/v1/filings?form_type=S-1&filed_from=${DATE_FROM}&limit=25" | jq -r '
  .data[] | "  \(.filed_date // .filed)  \((.company_name // .entity_name // .name // "?"))  \(.accession)"'

echo
if [ -n "$INDUSTRY" ]; then
  echo "=== Form D raises  (industry~${INDUSTRY}, min \$1M) ==="
  Q="/v1/raises?industry=$(printf %s "$INDUSTRY" | jq -sRr @uri)&min_amount=1000000&limit=25"
else
  echo "=== Form D raises  (state=CA, min \$1M) ==="
  Q="/v1/raises?state=CA&min_amount=1000000&limit=25"
fi
clous_get "$Q" | jq -r '
  .data[] | "  \(.filed_at)  \(.issuer_name)  [\(.investment_fund_type // .industry_group // "")]  offered $\(.total_offering_amount // 0)"'
