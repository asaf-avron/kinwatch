from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from kinwatch.models import RingEvent
from kinwatch.names import public_name
from kinwatch.ring.hmac import verify_webhook_signature


class WebhookRejected(ValueError):
    pass


def parse_event(payload: dict[str, Any]) -> RingEvent:
    meta = payload.get("meta") or {}
    data = payload.get("data") or {}
    attrs = data.get("attributes") or {}
    request_id = str(meta.get("request_id") or data.get("id") or "")
    if not request_id:
        raise WebhookRejected("missing request_id")
    occurred = meta.get("time") or datetime.now(timezone.utc).isoformat()
    if isinstance(occurred, str):
        occurred_at = datetime.fromisoformat(occurred.replace("Z", "+00:00"))
    else:
        occurred_at = datetime.now(timezone.utc)
    device_id = str(attrs.get("device_id") or data.get("id") or "unknown")
    name = public_name(attrs.get("name"), "a Ring device")
    event_type = str(data.get("type") or attrs.get("event_type") or "unknown")
    return RingEvent(
        request_id=request_id,
        event_type=event_type,
        device_id=device_id,
        device_name=name,
        occurred_at=occurred_at,
        raw=payload,
    )


def verify_and_parse(signing_key: str, raw_body: bytes, signature: str, payload: dict[str, Any]) -> RingEvent:
    if not verify_webhook_signature(signing_key, raw_body, signature):
        raise WebhookRejected("bad hmac")
    return parse_event(payload)
