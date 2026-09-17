from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from kinwatch.memory.store import HouseholdStore
from kinwatch.models import Policy, Visitor
from kinwatch.names import public_name, strip_ids
from kinwatch.policy import brief_incident, fuse_event, policy_actions
from kinwatch.ring.client import RingClient
from kinwatch.ring.fixtures import FRONT_DOOR_ID, NIGHT_OPEN_EVENTS
from kinwatch.ring.webhooks import parse_event
from kinwatch.settings import Settings
from kinwatch.vision import classify_snapshot
from kinwatch.widgets import live_view_html, timeline_html, visitor_html

FORBIDDEN_TOOLS = {"set_lock_state", "lock_door", "unlock_door", "set_lock"}


class KinwatchRuntime:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.store = HouseholdStore(self.settings)
        self.ring = RingClient(self.settings)

    def tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "list_devices", "description": "List household Ring devices by the names people gave them."},
            {"name": "get_device_status", "description": "Online/offline for a device, looked up by name."},
            {"name": "get_snapshot", "description": "Privacy-safe snapshot. Privacy-zone video is blacked out and never stored raw."},
            {"name": "get_event_history", "description": "Camera/doorbell Event History. Sensors have none — use household memory."},
            {"name": "get_live_view", "description": "Start a WHEP live view session for a named camera or doorbell."},
            {"name": "play_chime", "description": "Play the household chime: I'm looking / I'm coming. The only partner write."},
            {"name": "list_incidents", "description": "Fused doorstep incidents from doorbell + camera + contact sensor."},
            {"name": "get_incident", "description": "One incident with briefing and vision."},
            {"name": "brief_household", "description": "Plain-language brief of the latest incident."},
            {"name": "get_policy", "description": "Household quiet hours and escalation rules."},
            {"name": "set_policy", "description": "Update household policy."},
            {"name": "remember_visitor", "description": "Family labels a recurring visitor."},
            {"name": "delete_household_data", "description": "In-app data deletion."},
            {"name": "inject_demo_incident", "description": "Fixture: night doorbell + door open for the 3-minute video."},
        ]

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = arguments or {}
        if name in FORBIDDEN_TOOLS:
            return {"error": "Kinwatch cannot lock or unlock doors. The Ring Partner API has no lock actuation."}
        handler = self._handlers().get(name)
        if not handler:
            return {"error": f"unknown tool {name}"}
        return handler(arguments)

    def _handlers(self) -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
        return {
            "list_devices": lambda a: {
                "devices": [
                    {"name": d.name, "kind": d.kind, "online": d.online} for d in self.ring.list_devices()
                ]
            },
            "get_device_status": self._status,
            "get_snapshot": self._snapshot,
            "get_event_history": self._history,
            "get_live_view": self._live,
            "play_chime": lambda a: self.ring.play_chime(audio_ref=a.get("audio_ref")),
            "list_incidents": lambda a: {
                "incidents": [self._public_incident(i) for i in self.store.incidents()]
            },
            "get_incident": self._get_incident,
            "brief_household": self._brief,
            "get_policy": lambda a: self.store.policy().model_dump(),
            "set_policy": self._set_policy,
            "remember_visitor": self._remember,
            "delete_household_data": self._delete,
            "inject_demo_incident": lambda a: self.inject_demo(),
        }

    def ingest_event_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = parse_event(payload)
        if self.store.seen(event.request_id):
            return {"duplicate": True, "request_id": event.request_id}
        self.store.remember_request(event.request_id)
        self.store.add_event(event)
        incident = fuse_event(self.store, event, self.settings)
        doorbell = next((d for d in self.ring.list_devices() if d.kind in {"doorbell", "camera"}), None)
        if doorbell:
            snap = self.ring.snapshot(doorbell.id)
            vision = classify_snapshot(snap, self.settings)
            incident = self.store.attach_vision(incident.id, vision) or incident
            incident.briefing = brief_incident(incident, self.store, self.settings)
            self.store.upsert_incident(incident)
        actions = policy_actions(incident, self.store, self.settings)
        return {
            "duplicate": False,
            "request_id": event.request_id,
            "incident": self._public_incident(incident),
            "actions": actions,
        }

    def inject_demo(self) -> dict[str, Any]:
        results = [self.ingest_event_payload(payload) for payload in NIGHT_OPEN_EVENTS]
        latest = self.store.incidents()[0] if self.store.incidents() else None
        return {"ok": True, "results": results, "briefing": latest.briefing if latest else ""}

    def widget(self, kind: str) -> str:
        incidents = self.store.incidents()
        latest = incidents[0] if incidents else None
        visitors = self.store.visitors()
        visitor = visitors[-1] if visitors else None
        if kind == "timeline":
            return timeline_html(incidents)
        if kind == "live-view":
            doorbell = next((d for d in self.ring.list_devices() if d.kind in {"doorbell", "camera"}), None)
            whep = self.ring.start_whep(doorbell.id if doorbell else FRONT_DOOR_ID)
            caption = latest.vision.summary if latest and latest.vision else "Empty porch. Door ajar."
            return live_view_html(doorbell.name if doorbell else "the door", str(whep.get("location") or ""), caption)
        return visitor_html(visitor, latest)

    def _status(self, arguments: dict[str, Any]) -> dict[str, Any]:
        name = public_name(str(arguments.get("name") or ""))
        device = self.ring.device_by_name(name) or next(
            (d for d in self.ring.list_devices() if name.lower() in d.name.lower()), None
        )
        if not device:
            return {"error": "No device with that name. Open the Ring app to rename devices."}
        return {"name": device.name, "kind": device.kind, "online": device.online}

    def _snapshot(self, arguments: dict[str, Any]) -> dict[str, Any]:
        device = self._named_or_doorbell(str(arguments.get("name") or ""))
        snap = self.ring.snapshot(device.id)
        vision = classify_snapshot(snap, self.settings)
        return {
            "device_name": snap.device_name,
            "privacy_zones_applied": snap.privacy_zones_applied,
            "bytes": len(snap.image_png),
            "vision": vision.model_dump(),
        }

    def _history(self, arguments: dict[str, Any]) -> dict[str, Any]:
        device = self._named_or_doorbell(str(arguments.get("name") or ""))
        if device.kind in {"sensor", "chime"}:
            return {
                "device_name": device.name,
                "events": [],
                "note": "This device has no Ring Event History. Kinwatch memory is the record.",
            }
        return {"device_name": device.name, "events": self.ring.event_history(device.id)}

    def _live(self, arguments: dict[str, Any]) -> dict[str, Any]:
        device = self._named_or_doorbell(str(arguments.get("name") or ""))
        whep = self.ring.start_whep(device.id)
        return {"device_name": device.name, "whep": whep, "privacy_note": "Privacy-zone video is not shown."}

    def _get_incident(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._public_incident(self.store.get_incident(str(arguments.get("id") or arguments.get("incident_id") or "")))

    def _brief(self, arguments: dict[str, Any]) -> dict[str, Any]:
        incidents = self.store.incidents()
        if not incidents:
            return {"briefing": "Nothing at the door yet. I am watching."}
        incident = incidents[0]
        text = brief_incident(incident, self.store, self.settings)
        return {"briefing": strip_ids(text), "incident_id": incident.id}

    def _set_policy(self, arguments: dict[str, Any]) -> dict[str, Any]:
        current = self.store.policy().model_dump()
        current.update({k: v for k, v in arguments.items() if v is not None and k in Policy.model_fields})
        policy = self.store.set_policy(Policy.model_validate(current))
        return policy.model_dump()

    def _remember(self, arguments: dict[str, Any]) -> dict[str, Any]:
        visitor = Visitor(
            name=str(arguments.get("name") or "Someone"),
            notes=str(arguments.get("notes") or ""),
            last_seen=datetime.now(timezone.utc),
        )
        saved = self.store.remember_visitor(visitor)
        return saved.model_dump(mode="json")

    def _delete(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self.store.delete_all()
        return {"ok": True, "deleted": True}

    def _named_or_doorbell(self, name: str):
        if name:
            found = self.ring.device_by_name(name)
            if found:
                return found
        return next(d for d in self.ring.list_devices() if d.kind in {"doorbell", "camera"})

    def _public_incident(self, incident) -> dict[str, Any]:
        if incident is None:
            return {"error": "incident not found"}
        data = incident.model_dump(mode="json")
        data.pop("id", None)
        data["incident_id"] = incident.id if incident.id.startswith("inc-") else "incident"
        data["briefing"] = strip_ids(incident.briefing)
        return data
