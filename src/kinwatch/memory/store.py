from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from kinwatch.models import Incident, Policy, RingEvent, Visitor, VisionResult
from kinwatch.settings import Settings


class HouseholdStore:
    """File-backed household memory. DynamoDB is used when KINWATCH_DDB_TABLE is set."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.root = settings.ensure_data_dir()
        self.path = self.root / "household.json"
        self._ddb = None
        if settings.ddb_table:
            try:
                import boto3

                self._ddb = boto3.resource("dynamodb", region_name=settings.aws_region).Table(settings.ddb_table)
            except Exception:
                self._ddb = None
        self.state = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.is_file():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {
            "events": [],
            "incidents": [],
            "policy": Policy().model_dump(),
            "visitors": [],
            "seen_request_ids": [],
            "door_open": False,
            "notifications_hour": {"hour": "", "count": 0},
        }

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.state, default=str, indent=2), encoding="utf-8")
        if self._ddb is not None:
            try:
                self._ddb.put_item(Item={"pk": "household", "sk": "state", "doc": json.dumps(self.state, default=str)})
            except Exception:
                pass

    def seen(self, request_id: str) -> bool:
        return request_id in self.state["seen_request_ids"]

    def remember_request(self, request_id: str) -> None:
        ids: list[str] = self.state["seen_request_ids"]
        if request_id not in ids:
            ids.append(request_id)
            self.state["seen_request_ids"] = ids[-500:]
            self._save()

    def add_event(self, event: RingEvent) -> None:
        self.state["events"].append(event.model_dump(mode="json"))
        self.state["events"] = self.state["events"][-400:]
        if event.event_type in {"contact_open", "sensor_open"}:
            self.state["door_open"] = True
        if event.event_type in {"contact_close", "sensor_close"}:
            self.state["door_open"] = False
        self._save()

    def events(self) -> list[RingEvent]:
        return [RingEvent.model_validate(row) for row in self.state.get("events") or []]

    def policy(self) -> Policy:
        return Policy.model_validate(self.state.get("policy") or {})

    def set_policy(self, policy: Policy) -> Policy:
        self.state["policy"] = policy.model_dump()
        self._save()
        return policy

    def incidents(self) -> list[Incident]:
        return [Incident.model_validate(row) for row in self.state.get("incidents") or []]

    def upsert_incident(self, incident: Incident) -> Incident:
        rows = [i for i in self.incidents() if i.id != incident.id]
        rows.append(incident)
        rows.sort(key=lambda i: i.updated_at, reverse=True)
        self.state["incidents"] = [i.model_dump(mode="json") for i in rows[:100]]
        self._save()
        return incident

    def get_incident(self, incident_id: str) -> Incident | None:
        return next((i for i in self.incidents() if i.id == incident_id), None)

    def door_open(self) -> bool:
        return bool(self.state.get("door_open"))

    def remember_visitor(self, visitor: Visitor) -> Visitor:
        rows = [Visitor.model_validate(v) for v in self.state.get("visitors") or []]
        rows = [v for v in rows if v.name.lower() != visitor.name.lower()]
        rows.append(visitor)
        self.state["visitors"] = [v.model_dump(mode="json") for v in rows]
        self._save()
        return visitor

    def visitors(self) -> list[Visitor]:
        return [Visitor.model_validate(v) for v in self.state.get("visitors") or []]

    def can_notify(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        hour = now.strftime("%Y-%m-%dT%H")
        bucket = self.state.get("notifications_hour") or {"hour": "", "count": 0}
        if bucket.get("hour") != hour:
            bucket = {"hour": hour, "count": 0}
        allowed = bucket["count"] < self.policy().max_notifications_per_hour
        if allowed:
            bucket["count"] = int(bucket["count"]) + 1
            self.state["notifications_hour"] = bucket
            self._save()
        return allowed

    def delete_all(self) -> None:
        if self.path.exists():
            self.path.unlink()
        self.state = {
            "events": [],
            "incidents": [],
            "policy": Policy().model_dump(),
            "visitors": [],
            "seen_request_ids": [],
            "door_open": False,
            "notifications_hour": {"hour": "", "count": 0},
        }
        self._save()

    def attach_vision(self, incident_id: str, vision: VisionResult) -> Incident | None:
        incident = self.get_incident(incident_id)
        if not incident:
            return None
        incident.vision = vision
        incident.updated_at = datetime.now(timezone.utc)
        return self.upsert_incident(incident)
