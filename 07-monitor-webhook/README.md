# 07 · Monitor + webhook (with HMAC verification)

Create a standing **monitor**, register a **webhook** endpoint, and verify the
**HMAC signature** on every delivery.

## The pieces

| File | What it does |
| --- | --- |
| `create_monitor.py` / `monitor_webhook.sh` | Register an endpoint + create a monitor wired to it |
| `receiver.py` | A stdlib HTTP server that **verifies the signature** and prints events |
| `test_signature.py` | Offline check of the verification logic — no network, no key |

## Flow

1. **Register an endpoint** — `POST /v1/webhooks/endpoints` with an `https://` URL.
   The response includes a `secret`, returned **once** — store it.
2. **Create a monitor** — `POST /v1/monitors` with `target_type`/`target_value`
   (e.g. ticker `NVDA`), optional `signals` (event types), `materiality`, and the
   `webhook_endpoint_id` from step 1.
3. **Receive + verify** — when an event matches, Clous POSTs it to your URL.

A monitor fires only when an event matches **all** of: the **target**, a **signal**
in its list (empty = all), and **materiality** at or above its threshold.

## Verifying the signature

Clous sends these headers on each delivery:

| Header | Meaning |
| --- | --- |
| `Clous-Event-Id` | The event id |
| `Clous-Delivery-Id` | Unique per attempt — use for **idempotency** |
| `Clous-Timestamp` | ISO-8601, part of the signed payload |
| `Clous-Signature` | `sha256=<hex>` |

The signature is `HMAC-SHA256("{timestamp}.{raw_body}")` keyed by your endpoint
secret. Recompute it over the **exact raw bytes** you received and compare in
constant time:

```python
import hmac, hashlib

def verify(secret, timestamp, raw_body: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(
        secret.encode(), f"{timestamp}.{raw_body.decode()}".encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

Also reject **stale timestamps** (replay protection) and **dedupe** on
`Clous-Delivery-Id`. Always return `2xx` quickly — non-2xx deliveries are retried
with backoff (1 min → 5 min → 30 min → 2 h, then failed).

## Run

```bash
# 0. Sanity-check the verifier offline (no key needed)
python test_signature.py

# 1. Start the receiver locally and expose it over HTTPS
export CLOUS_WEBHOOK_SECRET=<secret-you-will-get-in-step-2>
python receiver.py 8080
#   in another shell:  ngrok http 8080   -> https://<id>.ngrok.io

# 2. Register endpoint + monitor (use the public HTTPS URL)
export CLOUS_API_KEY=clous_live_...
python create_monitor.py https://<id>.ngrok.io NVDA
#   copy the printed secret into CLOUS_WEBHOOK_SECRET and restart receiver.py

# Inspect deliveries any time:
#   GET /v1/webhooks/deliveries
```

Reference: [docs.clous.ai/api/monitors](https://docs.clous.ai/api/monitors) ·
[docs.clous.ai/api/webhooks](https://docs.clous.ai/api/webhooks).
