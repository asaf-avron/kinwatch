"""Never show Ring device IDs (`ava1.ring.device…`) in the companion UI."""

from __future__ import annotations

import re

DEVICE_ID_RE = re.compile(r"ava1\.ring\.(?:device|account|component)[.\w-]*", re.I)


def public_name(name: str | None, fallback: str = "the door") -> str:
    raw = (name or "").strip() or fallback
    if DEVICE_ID_RE.search(raw):
        return fallback
    return raw


def strip_ids(text: str) -> str:
    return DEVICE_ID_RE.sub("the device", text)
