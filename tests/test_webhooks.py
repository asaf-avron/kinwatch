import hashlib
import hmac
import json

from kinwatch.ring.fixtures import NIGHT_OPEN_EVENTS


def _sig(key: str, body: bytes) -> str:
    return "sha256=" + hmac.new(key.encode(), body, hashlib.sha256).hexdigest()


def test_webhook_200_after_persist(client, hmac_key):
    payload = NIGHT_OPEN_EVENTS[0]
    body = json.dumps(payload, separators=(",", ":")).encode()
    res = client.post("/webhooks/ring", content=body, headers={"X-Signature": _sig(hmac_key, body), "Content-Type": "application/json"})
    assert res.status_code == 200
    data = res.json()
    assert data["duplicate"] is False
    assert "incident" in data


def test_webhook_idempotent_request_id(client, hmac_key):
    payload = NIGHT_OPEN_EVENTS[0]
    body = json.dumps(payload).encode()
    headers = {"X-Signature": _sig(hmac_key, body), "Content-Type": "application/json"}
    first = client.post("/webhooks/ring", content=body, headers=headers)
    second = client.post("/webhooks/ring", content=body, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["duplicate"] is True


def test_webhook_rejects_bad_hmac(client):
    payload = NIGHT_OPEN_EVENTS[0]
    body = json.dumps(payload).encode()
    res = client.post("/webhooks/ring", content=body, headers={"X-Signature": "sha256=deadbeef", "Content-Type": "application/json"})
    assert res.status_code == 401


def test_demo_injector_fuses_doorbell_and_sensor(client):
    res = client.post("/demo/inject")
    assert res.status_code == 200
    briefing = res.json()["briefing"].lower()
    assert "door" in briefing
    incidents = client.get("/api/brief").json()
    assert "door" in incidents["briefing"].lower()
