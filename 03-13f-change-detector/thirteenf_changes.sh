#!/usr/bin/env bash
# 13F change detector in curl + jq.
# Diffs a manager's two most recent reporting periods by CUSIP.
#
#   export CLOUS_API_KEY=clous_live_...
#   ./thirteenf_changes.sh Berkshire
set -euo pipefail
source "$(dirname "$0")/../_shared/clous.sh"

MANAGER="${1:-Berkshire}"

# Pull a big slice of holdings (single page up to 100; bump/​paginate for full books).
ALL=$(clous_get "/v1/holdings?manager=$(printf %s "$MANAGER" | jq -sRr @uri)&limit=100")

# The two most recent periods present in the data.
PERIODS=$(echo "$ALL" | jq -r '[.data[].period] | unique | sort_by(
  (. | split("-") | (.[2]|tonumber)*100 +
    ({JAN:1,FEB:2,MAR:3,APR:4,MAY:5,JUN:6,JUL:7,AUG:8,SEP:9,OCT:10,NOV:11,DEC:12}[.[1]] // 0))
) | reverse')
CURR=$(echo "$PERIODS" | jq -r '.[0] // empty')
PREV=$(echo "$PERIODS" | jq -r '.[1] // empty')

if [ -z "$PREV" ]; then
  echo "Need two reporting periods to diff; found: $PERIODS"
  exit 0
fi

echo "Manager match: ${MANAGER}"
echo "Compare: ${PREV} -> ${CURR}"
echo

echo "== NEW positions (in ${CURR}, absent in ${PREV}) =="
echo "$ALL" | jq -r --arg c "$CURR" --arg p "$PREV" '
  ([.data[] | select(.period==$p) | .cusip]) as $prev |
  .data[] | select(.period==$c and (.cusip as $x | $prev | index($x) | not)) |
  "  \(.issuer)  \(.shares) sh  $\(.value_usd)"' | head -20

echo
echo "== EXITED (in ${PREV}, absent in ${CURR}) =="
echo "$ALL" | jq -r --arg c "$CURR" --arg p "$PREV" '
  ([.data[] | select(.period==$c) | .cusip]) as $curr |
  .data[] | select(.period==$p and (.cusip as $x | $curr | index($x) | not)) |
  "  \(.issuer)  was \(.shares) sh"' | head -20
