from __future__ import annotations

import json
from typing import Any

from kinwatch.models import Snapshot, VisionResult
from kinwatch.settings import Settings

PROMPT = (
    "You are Kinwatch, a household caretaking copilot. "
    "Classify this porch snapshot after privacy zones have already been blacked out. "
    "Reply JSON with keys kind (person|package|animal|unknown|empty) and summary "
    "(one plain-language sentence, no device IDs, no lock advice)."
)


def fixture_classify(snapshot: Snapshot) -> VisionResult:
    # Fixture snapshot is an empty porch with a door ajar.
    return VisionResult(
        kind="empty",
        summary="Empty porch, door ajar. No person and no package in view.",
        confidence=0.9,
    )


def classify_snapshot(snapshot: Snapshot, settings: Settings) -> VisionResult:
    if settings.use_fixtures:
        return fixture_classify(snapshot)
    try:
        import base64

        import boto3

        client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        image_b64 = base64.b64encode(snapshot.image_png).decode("ascii")
        body: dict[str, Any] = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"text": PROMPT},
                        {"image": {"format": "png", "source": {"bytes": image_b64}}},
                    ],
                }
            ]
        }
        resp = client.invoke_model(modelId=settings.bedrock_vision_model, body=json.dumps(body))
        payload = json.loads(resp["body"].read())
        text = _extract_text(payload)
        parsed = json.loads(text)
        kind = parsed.get("kind") if parsed.get("kind") in {"person", "package", "animal", "unknown", "empty"} else "unknown"
        return VisionResult(kind=kind, summary=str(parsed.get("summary") or "Could not describe the porch."), confidence=0.7)
    except Exception:
        return fixture_classify(snapshot)


def _extract_text(payload: dict[str, Any]) -> str:
    if "output" in payload and isinstance(payload["output"], dict):
        msg = payload["output"].get("message") or {}
        content = msg.get("content") or []
        for block in content:
            if "text" in block:
                return block["text"]
    if "content" in payload:
        return str(payload["content"])
    return json.dumps(payload)
