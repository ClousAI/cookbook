#!/usr/bin/env bash
# Earnings Q&A in curl + jq.
#
#   export CLOUS_API_KEY=clous_live_...
#   ./earnings_qa.sh NVDA "How did data center revenue trend last quarter?"
set -euo pipefail
source "$(dirname "$0")/../_shared/clous.sh"

TICKER="${1:-NVDA}"
Q="${2:-Summarize the most recent quarterly results and key risks.}"

echo "=== /v1/answer (grounded + cited) ==="
clous_post "/v1/answer" "$(jq -n --arg q "$Q" --arg t "$TICKER" '{
  q: $q, ticker: $t, forms: "10-Q,10-K,8-K", max_sources: 6
}')" | jq '{answer: (.answer // .text), basis, citations: (.citations // .sources)}'

echo
echo "=== /v1/answer with output_schema (structured) ==="
clous_post "/v1/answer" "$(jq -n --arg t "$TICKER" '{
  q: "What was total revenue in the most recent reported quarter, and the YoY change?",
  ticker: $t,
  forms: "10-Q,10-K",
  output_schema: {
    type: "object",
    properties: {
      metric:     {type: "string"},
      value:      {type: "string"},
      period:     {type: "string"},
      yoy_change: {type: "string"}
    },
    required: ["metric","value"]
  }
}')" | jq '.answer // .'

echo
echo "=== /v1/chat/completions (OpenAI-compatible, model=clous) ==="
clous_post "/v1/chat/completions" "$(jq -n --arg t "$TICKER" --arg q "$Q" '{
  model: "clous",
  messages: [ { role: "user", content: ("For " + $t + ": " + $q) } ]
}')" | jq '{answer: .choices[0].message.content, clous}'
