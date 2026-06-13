#!/usr/bin/env python3
"""
Create a webhook endpoint + a monitor, wired together.

Flow:
  1. POST /v1/webhooks/endpoints   — register your HTTPS receiver, get a `secret`
                                     (returned ONCE — store it to verify signatures).
  2. POST /v1/monitors             — a standing watch on a ticker/CIK/form/event_type,
                                     pointing at the endpoint from step 1.

When a matching event fires, Clous POSTs the event to your URL with an HMAC
signature. See receiver.py for verification.

Run:
    export CLOUS_API_KEY=clous_live_...
    python create_monitor.py https://your-host.example.com/webhooks/clous NVDA
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
import clous  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python create_monitor.py <https-webhook-url> [TICKER]")
    url = sys.argv[1]
    ticker = (sys.argv[2] if len(sys.argv) > 2 else "NVDA").upper()

    if not url.startswith("https://"):
        sys.exit("Webhook URL must be https:// — Clous rejects non-HTTPS endpoints.")

    # 1. Register the webhook endpoint.
    ep_resp = clous.post(
        "/v1/webhooks/endpoints",
        {"url": url, "description": f"Cookbook monitor for {ticker}"},
    )
    endpoint = (ep_resp.get("data") or [ep_resp])[0]
    endpoint_id = endpoint["id"]
    secret = endpoint.get("secret")
    print(f"Registered endpoint {endpoint_id}")
    print(f"  url    : {endpoint['url']}")
    print(f"  secret : {secret}")
    print("  ^ store this secret now — it is shown ONCE and signs every delivery.\n")

    # 2. Create the monitor, attached to that endpoint.
    mon_resp = clous.post(
        "/v1/monitors",
        {
            "name": f"{ticker} material changes",
            "target_type": "ticker",
            "target_value": ticker,
            # Empty/omitted signals = every event for the target.
            "signals": [
                "sec.filing.new",
                "sec.8k.executive_change",
                "sec.8k.material_agreement",
                "sec.form4.insider_sell",
            ],
            "materiality": "medium",          # fire on medium+ importance
            "webhook_endpoint_id": endpoint_id,
        },
    )
    monitor = (mon_resp.get("data") or [mon_resp])[0]
    print(f"Created monitor {monitor['id']}  ({monitor['name']})")
    print(f"  watching {monitor['target_type']}={monitor['target_value']} "
          f"signals={monitor.get('signals')} materiality={monitor.get('materiality')}")

    print("\nNext:")
    print("  - Run receiver.py on a public HTTPS host at the URL above.")
    print("  - Inspect deliveries: GET /v1/webhooks/deliveries")
    print("  - Pause without deleting: PATCH /v1/monitors/<id> {\"status\":\"paused\"}")


if __name__ == "__main__":
    main()
