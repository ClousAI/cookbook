#!/usr/bin/env python3
"""
Offline sanity check for the HMAC verification logic — no network, no API key.

Signs a fake payload with a known secret exactly as Clous does, then asserts that
receiver.verify() accepts it and rejects a tampered body. Useful to confirm your
verification is correct before pointing a real monitor at it.

Run:
    python test_signature.py
"""
import hashlib
import hmac
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from receiver import verify, timestamp_fresh  # noqa: E402

SECRET = "test_secret_9bccb20ea569"


def sign(secret: str, timestamp: str, raw_body: bytes) -> str:
    return "sha256=" + hmac.new(
        secret.encode(), f"{timestamp}.{raw_body.decode()}".encode(), hashlib.sha256
    ).hexdigest()


def main() -> None:
    ts = datetime.now(timezone.utc).isoformat()
    body = b'{"type":"sec.filing.new","event":{"id":"abc","summary":"NVIDIA filed a 10-Q"}}'
    sig = sign(SECRET, ts, body)

    assert verify(SECRET, ts, body, sig), "valid signature should verify"
    assert timestamp_fresh(ts), "fresh timestamp should pass"
    assert not verify(SECRET, ts, body + b" ", sig), "tampered body must fail"
    assert not verify("wrong_secret", ts, body, sig), "wrong secret must fail"
    assert not timestamp_fresh("2000-01-01T00:00:00+00:00"), "stale timestamp must fail"

    print("All signature-verification checks passed.")


if __name__ == "__main__":
    main()
