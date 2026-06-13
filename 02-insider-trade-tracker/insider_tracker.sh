#!/usr/bin/env bash
# Insider-trade tracker in curl + jq.
#
#   export CLOUS_API_KEY=clous_live_...
#   ./insider_tracker.sh NVDA
set -euo pipefail
source "$(dirname "$0")/../_shared/clous.sh"

TICKER="${1:-NVDA}"
# 90 days back (GNU date; on macOS use: date -v-90d +%Y-%m-%d)
DATE_FROM=$(date -u -d '90 days ago' +%Y-%m-%d 2>/dev/null || date -u -v-90d +%Y-%m-%d)

echo "Recent insider transactions for ${TICKER} since ${DATE_FROM}"
echo

# Classify each row by SEC transaction code: P=buy, S=sell, else show the code.
clous_get "/v1/insider?ticker=${TICKER}&date_from=${DATE_FROM}&limit=100" | jq -r '
  .data[] |
  [ .trans_date,
    (if .trans_code=="P" then "BUY" elif .trans_code=="S" then "SELL" else .trans_code end),
    (.owner_name // "" | .[0:26]),
    (.shares // 0 | tostring),
    (.value_usd // 0 | tostring)
  ] | @tsv' | column -t -s $'\t'

echo
echo "== Cluster check: distinct open-market buyers vs sellers =="
clous_get "/v1/insider?ticker=${TICKER}&date_from=${DATE_FROM}&trans_code=P&limit=100" \
  | jq -r '"open-market BUYERS : \([.data[].owner_name] | unique | length)"'
clous_get "/v1/insider?ticker=${TICKER}&date_from=${DATE_FROM}&trans_code=S&limit=100" \
  | jq -r '"open-market SELLERS: \([.data[].owner_name] | unique | length)"'
echo "(3+ distinct insiders on one side within the window = a cluster signal.)"
