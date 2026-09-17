from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

ArrivalKind = Literal["person", "package", "animal", "unknown", "empty"]


class DeviceView(BaseModel):
    id: str
    name: str
    kind: Literal["doorbell", "camera", "sensor", "chime", "unknown"] = "unknown"
    online: bool = True
    capabilities: dict[str, Any] = Field(default_factory=dict)


class PrivacyZone(BaseModel):
    id: str
    vertices: list[tuple[float, float]]


class Snapshot(BaseModel):
    device_id: str
    device_name: str
    image_png: bytes
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    privacy_zones_applied: bool = True


class RingEvent(BaseModel):
    request_id: str
    event_type: str
    device_id: str
    device_name: str
    occurred_at: datetime
    raw: dict[str, Any] = Field(default_factory=dict)


class VisionResult(BaseModel):
    kind: ArrivalKind
    summary: str
    confidence: float = 0.5


class Incident(BaseModel):
    id: str
    title: str
    started_at: datetime
    updated_at: datetime
    device_names: list[str] = Field(default_factory=list)
    event_types: list[str] = Field(default_factory=list)
    door_open: bool | None = None
    vision: VisionResult | None = None
    briefing: str = ""
    status: Literal["open", "watching", "resolved"] = "open"


class Policy(BaseModel):
    quiet_hours_start: str = "21:00"
    quiet_hours_end: str = "07:00"
    door_open_escalate_minutes: int = 2
    unanswered_doorbell_live_view: bool = True
    notify_family: bool = True
    max_notifications_per_hour: int = 4


class Visitor(BaseModel):
    name: str
    notes: str = ""
    last_seen: datetime | None = None
