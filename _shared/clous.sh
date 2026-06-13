# Shared bash/curl helpers for the cookbook. Source this file:
#   source ../_shared/clous.sh
#
# It defines:
#   clous_get  PATH [curl args...]   -> GET an endpoint with auth
#   clous_post PATH JSON             -> POST JSON to an endpoint with auth
#
# Requires: curl, and jq for the JSON-parsing examples.
# Reads CLOUS_API_KEY from the environment.

: "${CLOUS_BASE_URL:=https://api.clous.ai}"

clous_require_key() {
  if [ -z "${CLOUS_API_KEY:-}" ]; then
    echo "CLOUS_API_KEY is not set. Get a key at https://clous.ai then:" >&2
    echo "  export CLOUS_API_KEY=clous_live_..." >&2
    return 1
  fi
}

# clous_get "/v1/insider?ticker=AAPL&limit=5"
clous_get() {
  clous_require_key || return 1
  local path="$1"; shift
  curl -sS --fail-with-body \
    -H "Authorization: Bearer ${CLOUS_API_KEY}" \
    -H "Accept: application/json" \
    "$@" \
    "${CLOUS_BASE_URL}${path}"
}

# clous_post "/v1/monitors" '{"name":"...","target_type":"ticker","target_value":"NVDA"}'
clous_post() {
  clous_require_key || return 1
  local path="$1"; local body="$2"
  curl -sS --fail-with-body \
    -X POST \
    -H "Authorization: Bearer ${CLOUS_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "${body}" \
    "${CLOUS_BASE_URL}${path}"
}
