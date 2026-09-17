from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from kinwatch.memory.store import HouseholdStore
from kinwatch.models import Incident, Policy, RingEvent
from kinwatch.settings import Settings

FUSE_WINDOW = timedelta(minutes=3)


def _parse_hhmm(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def in_quiet_hours(policy: Policy, now: datetime, tz_name: str) -> bool:
    local = now.astimezone(ZoneInfo(tz_name))
    start = _parse_hhmm(policy.quiet_hours_start)
    end = _parse_hhmm(policy.quiet_hours_end)
    clock = local.timetz().replace(tzinfo=None)
    if start <= end:
        return start <= clock < end
    return clock >= start or clock < end


def fuse_event(store: HouseholdStore, event: RingEvent, settings: Settings) -> Incident:
    now = event.occurred_at if event.occurred_at.tzinfo else event.occurred_at.replace(tzinfo=timezone.utc)
    open_incidents = [i for i in store.incidents() if i.status != "resolved"]
    match = None
    for incident in open_incidents:
        if now - incident.updated_at <= FUSE_WINDOW:
            match = incident
            break
    if match is None:
        match = Incident(
            id=f"inc-{event.request_id}",
            title="Something happened at the door",
            started_at=now,
            updated_at=now,
        )
    names = list(match.device_names)
    if event.device_name not in names:
        names.append(event.device_name)
    match.device_names = names
    types = list(match.event_types)
    if event.event_type not in types:
        types.append(event.event_type)
    match.event_types = types
    match.updated_at = now
    if event.event_type in {"contact_open", "sensor_open"}:
        match.door_open = True
    if event.event_type in {"contact_close", "sensor_close"}:
        match.door_open = False
    match.briefing = brief_incident(match, store, settings, now)
    return store.upsert_incident(match)


def brief_incident(incident: Incident, store: HouseholdStore, settings: Settings, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    policy = store.policy()
    quiet = in_quiet_hours(policy, now, settings.household_tz)
    door = "open" if (incident.door_open if incident.door_open is not None else store.door_open()) else "closed"
    vision = incident.vision.summary if incident.vision else "Camera has not classified the porch yet."
    try:
        when = incident.started_at.astimezone(ZoneInfo(settings.household_tz)).strftime("%I:%M %p").lstrip("0")
    except Exception:
        when = ""
    place = incident.device_names[0] if incident.device_names else "the door"
    if incident.door_open and (incident.vision is None or incident.vision.kind == "empty"):
        line = f"{place} opened at {when}. No person on camera. Door still {door}."
    elif incident.vision and incident.vision.kind == "person":
        line = f"A person is at {place}. {vision}"
    elif incident.vision and incident.vision.kind == "package":
        line = f"A package is at {place}. {vision}"
    else:
        line = f"Activity at {place} at {when}. Door is {door}. {vision}"
    if quiet:
        line += " Quiet hours are on, so the house will stay calm unless you ask."
    return line


def policy_actions(incident: Incident, store: HouseholdStore, settings: Settings, now: datetime | None = None) -> list[str]:
    now = now or datetime.now(timezone.utc)
    policy = store.policy()
    actions: list[str] = []
    if "button_press" in incident.event_types and policy.unanswered_doorbell_live_view:
        actions.append("start_live_view")
        actions.append("brief_family")
    if incident.door_open:
        elapsed = (now - incident.started_at).total_seconds() / 60.0
        if elapsed >= policy.door_open_escalate_minutes:
            actions.append("escalate_door_open")
    if store.can_notify(now):
        actions.append("notify")
    else:
        actions.append("rate_limited")
    return actions
