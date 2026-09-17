from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw

from kinwatch.models import DeviceView, PrivacyZone, Snapshot
from kinwatch.names import public_name
from kinwatch.ring.privacy import apply_privacy_zones, parse_privacy_zones

FRONT_DOOR = "Mom's front door"
PORCH_CAM = "Porch camera"
DOOR_SENSOR = "Front door sensor"
HALL_CHIME = "Hall chime"

FRONT_DOOR_ID = "ava1.ring.device.FRONTDOOR"
PORCH_ID = "ava1.ring.device.PORCHCAM"
SENSOR_ID = "ava1.ring.device.DOORSENSOR"
CHIME_ID = "ava1.ring.device.HALLCHIME"

# A privacy zone covering the right 20% of the frame (neighbor's window). Never shown in UI.
FIXTURE_PRIVACY_ZONES = [
    PrivacyZone(id="neighbor-window", vertices=[(0.8, 0.0), (1.0, 0.0), (1.0, 1.0), (0.8, 1.0)]),
]


def _empty_porch_png() -> bytes:
    image = Image.new("RGB", (640, 360), (28, 32, 40))
    draw = ImageDraw.Draw(image)
    draw.rectangle([40, 80, 280, 340], outline=(180, 140, 90), width=8)  # door
    draw.rectangle([512, 40, 630, 200], fill=(90, 140, 200))  # neighbor window (privacy)
    draw.rectangle([300, 220, 500, 340], fill=(50, 55, 62))  # porch floor
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


FIXTURE_DEVICES: list[dict[str, Any]] = [
    {
        "id": FRONT_DOOR_ID,
        "name": FRONT_DOOR,
        "kind": "doorbell",
        "online": True,
        "capabilities": {"video": {"codecs": ["H264"]}, "button": True},
        "configurations": {
            "attributes": {"image_enhancements": {"privacy_zones": [{"id": "neighbor-window", "vertices": [{"x": 0.8, "y": 0.0}, {"x": 1.0, "y": 0.0}, {"x": 1.0, "y": 1.0}, {"x": 0.8, "y": 1.0}]}]}}
        },
    },
    {
        "id": PORCH_ID,
        "name": PORCH_CAM,
        "kind": "camera",
        "online": True,
        "capabilities": {"video": {"codecs": ["H264"]}},
        "configurations": {"attributes": {"image_enhancements": {"privacy_zones": []}}},
    },
    {
        "id": SENSOR_ID,
        "name": DOOR_SENSOR,
        "kind": "sensor",
        "online": True,
        "capabilities": {"sensor": True},
        "configurations": {},
    },
    {
        "id": CHIME_ID,
        "name": HALL_CHIME,
        "kind": "chime",
        "online": True,
        "capabilities": {"audio": {"supported_actions": ["chime.play"], "customizable_slots": 2}},
        "configurations": {
            "attributes": {
                "audio": {
                    "volume": 5,
                    "customizable_slots": [{"event": "kinwatch.looking", "audio_ref": "kinwatch-looking"}],
                }
            }
        },
    },
]

NIGHT_OPEN_EVENTS = [
    {
        "meta": {
            "version": "1.1",
            "time": "2026-10-12T09:11:00Z",
            "request_id": "demo-doorbell-211",
            "account_id": "ava1.ring.account.MOM",
        },
        "data": {
            "id": f"{FRONT_DOOR_ID}_button_press_211",
            "type": "button_press",
            "attributes": {"device_id": FRONT_DOOR_ID, "name": FRONT_DOOR},
        },
    },
    {
        "meta": {
            "version": "1.1",
            "time": "2026-10-12T09:11:04Z",
            "request_id": "demo-sensor-211",
            "account_id": "ava1.ring.account.MOM",
        },
        "data": {
            "id": f"{SENSOR_ID}_contact_open_211",
            "type": "contact_open",
            "attributes": {"device_id": SENSOR_ID, "name": DOOR_SENSOR, "open": True},
        },
    },
]


def fixture_device_views() -> list[DeviceView]:
    return [
        DeviceView(
            id=d["id"],
            name=public_name(d["name"]),
            kind=d["kind"],
            online=d["online"],
            capabilities=d["capabilities"],
        )
        for d in FIXTURE_DEVICES
    ]


def fixture_snapshot(device_id: str) -> Snapshot:
    device = next((d for d in FIXTURE_DEVICES if d["id"] == device_id), FIXTURE_DEVICES[0])
    zones = parse_privacy_zones(device.get("configurations"))
    raw = _empty_porch_png()
    safe = apply_privacy_zones(raw, zones)
    return Snapshot(
        device_id=device["id"],
        device_name=public_name(device["name"]),
        image_png=safe,
        captured_at=datetime.now(timezone.utc),
        privacy_zones_applied=True,
    )


def fixture_whep_sdp() -> str:
    return (
        "v=0\r\n"
        "o=- 0 0 IN IP4 127.0.0.1\r\n"
        "s=Kinwatch fixture WHEP\r\n"
        "t=0 0\r\n"
        "m=video 9 UDP/TLS/RTP/SAVPF 96\r\n"
        "c=IN IP4 0.0.0.0\r\n"
        "a=recvonly\r\n"
    )


def fixture_history(device_id: str) -> list[dict[str, Any]]:
    device = next((d for d in FIXTURE_DEVICES if d["id"] == device_id), None)
    if not device or device["kind"] in {"sensor", "chime"}:
        return []
    return [
        {
            "type": "button_press" if device["kind"] == "doorbell" else "motion_detected",
            "time": "2026-10-12T09:11:00Z",
            "device_name": public_name(device["name"]),
        }
    ]
