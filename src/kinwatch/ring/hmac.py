"""Ring HMAC: webhooks are hex `sha256=`; linking nonces are URL-safe Base64 without padding."""

from __future__ import annotations

import base64
import hashlib
import hmac


def verify_webhook_signature(signing_key: str, raw_body: bytes, received_signature: str) -> bool:
    expected = hmac.new(signing_key.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    received = (received_signature or "").strip()
    if received.lower().startswith("sha256="):
        received = received.split("=", 1)[1]
    return hmac.compare_digest(expected, received)


def linking_nonce(signing_key: str, timestamp_ms: str, account_id: str) -> str:
    payload = f"{timestamp_ms}:{account_id}".encode("utf-8")
    digest = hmac.new(signing_key.encode("utf-8"), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def verify_linking_nonce(signing_key: str, timestamp_ms: str, account_id: str, nonce: str) -> bool:
    expected = linking_nonce(signing_key, timestamp_ms, account_id)
    return hmac.compare_digest(expected, (nonce or "").strip())
