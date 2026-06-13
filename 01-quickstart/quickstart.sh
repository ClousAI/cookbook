#!/usr/bin/env bash
# Quickstart in pure curl + jq.
#
#   export CLOUS_API_KEY=clous_live_...
#   ./quickstart.sh
set -euo pipefail
source "$(dirname "$0")/../_shared/clous.sh"

echo "== 1. One authenticated call: 5 most recent Apple filings =="
# CIK 0000320193 = Apple Inc.
clous_get "/v1/filings?cik=0000320193&limit=5" | jq '{
  source, as_of,
  page,
  filings: [.data[] | {form_type, filed_date, accession}]
}'

echo
echo "== 2. The envelope: page object drives pagination =="
clous_get "/v1/filings?cik=0000320193&form_type=8-K&limit=3" | jq '.page'

echo
echo "== 3. Cursor pagination: fetch page 1, then follow next_cursor to page 2 =="
CURSOR=$(clous_get "/v1/filings?cik=0000320193&form_type=8-K&limit=3" | jq -r '.page.next_cursor')
echo "next_cursor = ${CURSOR}"
if [ "${CURSOR}" != "null" ] && [ -n "${CURSOR}" ]; then
  echo "Page 2 accessions:"
  clous_get "/v1/filings?cik=0000320193&form_type=8-K&limit=3&cursor=${CURSOR}" \
    | jq -r '.data[].accession'
fi
