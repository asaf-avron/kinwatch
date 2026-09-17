"""Exclude Ring privacy zones from display, analysis, and storage. Never return zone polygons to the UI."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw

from kinwatch.models import PrivacyZone


def parse_privacy_zones(config: dict[str, Any] | None) -> list[PrivacyZone]:
    if not config:
        return []
    attrs = config.get("attributes") if "attributes" in config else config
    image = (attrs or {}).get("image_enhancements") or (attrs or {}).get("video") or attrs or {}
    raw = image.get("privacy_zones") or []
    zones: list[PrivacyZone] = []
    for item in raw:
        verts = item.get("vertices") or item.get("points") or []
        points: list[tuple[float, float]] = []
        for v in verts:
            if isinstance(v, dict):
                points.append((float(v.get("x", 0)), float(v.get("y", 0))))
            elif isinstance(v, (list, tuple)) and len(v) >= 2:
                points.append((float(v[0]), float(v[1])))
        if points:
            zones.append(PrivacyZone(id=str(item.get("id") or f"z{len(zones)}"), vertices=points))
    return zones


def _to_pixels(vertices: list[tuple[float, float]], width: int, height: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for x, y in vertices:
        if 0 <= x <= 1 and 0 <= y <= 1:
            out.append((int(x * (width - 1)), int(y * (height - 1))))
        else:
            out.append((int(x), int(y)))
    return out


def apply_privacy_zones(image_bytes: bytes, zones: list[PrivacyZone]) -> bytes:
    if not zones:
        return image_bytes
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(image)
    for zone in zones:
        pts = _to_pixels(zone.vertices, image.width, image.height)
        if len(pts) >= 3:
            draw.polygon(pts, fill=(0, 0, 0))
        elif len(pts) == 2:
            draw.rectangle([pts[0], pts[1]], fill=(0, 0, 0))
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()
