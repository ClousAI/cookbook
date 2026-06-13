#!/usr/bin/env bash
# Create a webhook endpoint + monitor in curl + jq, then show how to read deliveries.
#
#   export CLOUS_API_KEY=clous_live_...
#   ./monitor_webhook.sh https://your-host.example.com/webhooks/clous NVDA
set -euo pipefail
source "$(dirname "$0")/../_shared/clous.sh"

URL="${1:?usage: ./monitor_webhook.sh <https-webhook-url> [TICKER]}"
TICKER="${2:-NVDA}"

echo "== 1. Register webhook endpoint =="
EP=$(clous_post "/v1/webhooks/endpoints" "$(jq -n --arg u "$URL" '{url:$u, description:"cookbook"}')")
echo "$EP" | jq '.data[0] | {id, url, secret, status}'
EP_ID=$(echo "$EP" | jq -r '.data[0].id')
echo "  ^ store the secret — shown once; it signs every delivery."
echo

echo "== 2. Create monitor pointing at that endpoint =="
clous_post "/v1/monitors" "$(jq -n --arg t "$TICKER" --arg ep "$EP_ID" '{
  name: ($t + " material changes"),
  target_type: "ticker",
  target_value: $t,
  signals: ["sec.filing.new","sec.8k.executive_change","sec.form4.insider_sell"],
  materiality: "medium",
  webhook_endpoint_id: $ep
}')" | jq '.data[0] | {id, name, target_value, signals, materiality, status}'

echo
echo "== 3. Inspect the delivery log =="
echo "   clous_get \"/v1/webhooks/deliveries?endpoint_id=${EP_ID}\""
echo
echo "Verify the signature on each delivery: HMAC-SHA256 of \"{Clous-Timestamp}.{raw_body}\""
echo "keyed by the endpoint secret, compared against the Clous-Signature header."
echo "See receiver.py for a runnable verifier."
