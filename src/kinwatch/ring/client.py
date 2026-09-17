from __future__ import annotations

from typing import Any

import httpx

from kinwatch.models import DeviceView, Snapshot
from kinwatch.names import public_name
from kinwatch.ring import fixtures
from kinwatch.ring.privacy import apply_privacy_zones, parse_privacy_zones
from kinwatch.settings import Settings


class RingClient:
    """Ring Partner API. Fixture mode is the default so judges can run without a token."""

    def __init__(self, settings: Settings, http: httpx.Client | None = None):
        self.settings = settings
        self._http = http

    @property
    def live(self) -> bool:
        return (not self.settings.use_fixtures) and bool(self.settings.ring_access_token)

    def _client(self) -> httpx.Client:
        if self._http is None:
            self._http = httpx.Client(timeout=20.0)
        return self._http

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.ring_access_token}",
            "Accept": "application/vnd.api+json, application/json",
        }

    def list_devices(self) -> list[DeviceView]:
        if not self.live:
            return fixtures.fixture_device_views()
        url = f"{self.settings.ring_api_base.rstrip('/')}/v1/devices"
        resp = self._client().get(
            url,
            params={"include": "status,capabilities,location,configurations"},
            headers=self._headers(),
        )
        resp.raise_for_status()
        payload = resp.json()
        included = {item.get("id"): item for item in payload.get("included") or [] if isinstance(item, dict)}
        views: list[DeviceView] = []
        for item in payload.get("data") or []:
            attrs = item.get("attributes") or {}
            rel = item.get("relationships") or {}
            status = _related(rel, included, "status")
            caps = _related(rel, included, "capabilities") or {}
            kind = _kind(caps)
            views.append(
                DeviceView(
                    id=str(item.get("id")),
                    name=public_name(attrs.get("name"), "a Ring device"),
                    kind=kind,
                    online=bool((status or {}).get("attributes", {}).get("online", True)),
                    capabilities=(caps.get("attributes") if caps else {}) or {},
                )
            )
        return views

    def device_by_name(self, name: str) -> DeviceView | None:
        needle = name.strip().lower()
        for device in self.list_devices():
            if device.name.lower() == needle:
                return device
        return None

    def configurations(self, device_id: str) -> dict[str, Any]:
        if not self.live:
            device = next((d for d in fixtures.FIXTURE_DEVICES if d["id"] == device_id), {})
            return device.get("configurations") or {}
        url = f"{self.settings.ring_api_base.rstrip('/')}/v1/devices/{device_id}/configurations"
        resp = self._client().get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json().get("data") or resp.json()

    def snapshot(self, device_id: str, component_id: int | None = 1) -> Snapshot:
        if not self.live:
            return fixtures.fixture_snapshot(device_id)
        url = f"{self.settings.ring_api_base.rstrip('/')}/v1/devices/{device_id}/media/image/download"
        body: dict[str, Any] = {}
        if component_id is not None:
            body = {"components": [{"component_id": component_id}]}
        resp = self._client().post(url, headers=self._headers(), json=body)
        resp.raise_for_status()
        zones = parse_privacy_zones(self.configurations(device_id))
        safe = apply_privacy_zones(resp.content, zones)
        device = next((d for d in self.list_devices() if d.id == device_id), None)
        return Snapshot(
            device_id=device_id,
            device_name=device.name if device else "the camera",
            image_png=safe,
            privacy_zones_applied=True,
        )

    def event_history(self, device_id: str) -> list[dict[str, Any]]:
        if not self.live:
            return fixtures.fixture_history(device_id)
        device = next((d for d in self.list_devices() if d.id == device_id), None)
        if device and device.kind in {"sensor", "chime"}:
            return []
        url = f"{self.settings.ring_api_base.rstrip('/')}/v1/history/devices/{device_id}/events"
        resp = self._client().get(url, headers=self._headers())
        resp.raise_for_status()
        payload = resp.json()
        return payload.get("data") or []

    def start_whep(self, device_id: str, offer_sdp: str = "", component_id: int | None = None) -> dict[str, Any]:
        if not self.live:
            return {
                "sdp": fixtures.fixture_whep_sdp(),
                "location": f"{self.settings.public_base_url}/whep/sessions/fixture",
                "status": 201,
            }
        url = f"{self.settings.ring_api_base.rstrip('/')}/v1/devices/{device_id}/media/streaming/whep/sessions"
        if component_id is not None:
            url += f"?component_id={component_id}"
        headers = {**self._headers(), "Content-Type": "application/sdp"}
        resp = self._client().post(url, headers=headers, content=(offer_sdp or fixtures.fixture_whep_sdp()).encode())
        return {
            "sdp": resp.text,
            "location": resp.headers.get("Location", ""),
            "status": resp.status_code,
        }

    def play_chime(self, device_id: str | None = None, audio_ref: str | None = None) -> dict[str, Any]:
        ref = audio_ref or self.settings.ring_audio_ref
        if not self.live:
            chime = next(d for d in fixtures.FIXTURE_DEVICES if d["kind"] == "chime")
            return {"ok": True, "device_name": chime["name"], "audio_ref": ref, "fixture": True}
        target = device_id or next(d.id for d in self.list_devices() if d.kind == "chime")
        url = f"{self.settings.ring_api_base.rstrip('/')}/v1/devices/{target}/media/audio/playback"
        body = {"data": {"type": "audio", "attributes": {"audio_ref": ref}}}
        resp = self._client().post(url, headers=self._headers(), json=body)
        resp.raise_for_status()
        device = next((d for d in self.list_devices() if d.id == target), None)
        return {"ok": True, "device_name": device.name if device else "the chime", "audio_ref": ref}


def _related(rel: dict[str, Any], included: dict[str, Any], key: str) -> dict[str, Any] | None:
    data = (rel.get(key) or {}).get("data") or {}
    rid = data.get("id") if isinstance(data, dict) else None
    if not rid:
        return None
    return included.get(rid)


def _kind(caps: dict[str, Any]) -> str:
    attrs = (caps or {}).get("attributes") or caps or {}
    audio = attrs.get("audio") or {}
    if "chime.play" in (audio.get("supported_actions") or []):
        return "chime"
    if attrs.get("sensor"):
        return "sensor"
    if attrs.get("button"):
        return "doorbell"
    if attrs.get("video"):
        return "camera"
    return "unknown"
