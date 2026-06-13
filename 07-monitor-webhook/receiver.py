#!/usr/bin/env python3
"""
Minimal webhook receiver that verifies the Clous HMAC signature.

Pure standard library — no Flask needed. Listens on a port, and for every POST:
  - reads the raw body (verification must use the EXACT bytes received)
  - recomputes the HMAC and compares in constant time
  - rejects stale timestamps (replay protection)
  - 200s good deliveries, 401s bad signatures

Delivery headers Clous sends:
  Clous-Event-Id     the event id
  Clous-Delivery-Id  unique per attempt — use for idempotency
  Clous-Timestamp    ISO-8601, part of the signed payload
  Clous-Signature    "sha256=<hex>" = HMAC-SHA256 of "{timestamp}.{raw_body}"
                     keyed by your endpoint secret

Run:
    export CLOUS_WEBHOOK_SECRET=<the secret from create_monitor.py>
    python receiver.py 8080

Then expose it over HTTPS (e.g. `ngrok http 8080`) and use that URL as the
webhook endpoint. For a quick local sanity check without a real delivery, run
test_signature.py.
"""
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

# Reject deliveries whose timestamp is older than this (replay protection).
MAX_SKEW_SECONDS = 300


def verify(secret: str, timestamp: str, raw_body: bytes, signature: str) -> bool:
    """Recompute the HMAC over '{timestamp}.{raw_body}' and constant-time compare."""
    expected = "sha256=" + hmac.new(
        secret.encode(),
        f"{timestamp}.{raw_body.decode()}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def timestamp_fresh(timestamp: str) -> bool:
    try:
        ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    return abs(age) <= MAX_SKEW_SECONDS


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 (stdlib naming)
        secret = os.environ.get("CLOUS_WEBHOOK_SECRET", "")
        if not secret:
            self._reply(500, "CLOUS_WEBHOOK_SECRET not set on the receiver")
            return

        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length)  # exact bytes — do NOT re-serialize

        timestamp = self.headers.get("Clous-Timestamp", "")
        signature = self.headers.get("Clous-Signature", "")
        delivery_id = self.headers.get("Clous-Delivery-Id", "")

        if not verify(secret, timestamp, raw_body, signature):
            print(f"[REJECT] bad signature (delivery {delivery_id})")
            self._reply(401, "invalid signature")
            return
        if not timestamp_fresh(timestamp):
            print(f"[REJECT] stale timestamp {timestamp} (delivery {delivery_id})")
            self._reply(401, "stale timestamp")
            return

        # Verified. Use Clous-Delivery-Id for idempotency before acting.
        payload = json.loads(raw_body.decode())
        event = payload.get("event", {})
        print(f"[OK] {payload.get('type')}  "
              f"{event.get('entity_name')} ({event.get('entity_ticker') or event.get('entity_cik')})  "
              f"importance={event.get('importance')}  delivery={delivery_id}")
        print(f"     summary: {event.get('summary')}")

        # Always 2xx promptly so Clous doesn't retry. Do heavy work async.
        self._reply(200, "ok")

    def _reply(self, code: int, msg: str):
        body = msg.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # silence default access logs
        pass


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    if not os.environ.get("CLOUS_WEBHOOK_SECRET"):
        print("warning: CLOUS_WEBHOOK_SECRET is not set — every delivery will 500.")
    print(f"Listening on 0.0.0.0:{port} (POST). Expose over HTTPS to receive deliveries.")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
