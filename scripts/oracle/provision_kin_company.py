#!/usr/bin/env python3
"""KIN Paperclip provision Phase D. Never prints secret values. Never copies host CURSOR_API_KEY."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import psycopg2

EXCL = {
    "94bea508-f6a9-44db-b44c-ff6a6974b3e5",
    "164be67f-99d2-4e4e-8573-e017d3805f8e",
    "2dfca2d5-4c80-4a9d-b5bb-19b9323c5a20",
}
API = "http://127.0.0.1:3100"


def read_env(path: Path, name: str) -> str | None:
    if not path.is_file():
        return None
    for line in path.read_text().splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip("\"'")
    return None


def decode_master(raw: str) -> bytes:
    trimmed = raw.strip()
    if len(trimmed) == 64 and all(c in "0123456789abcdefABCDEF" for c in trimmed):
        return bytes.fromhex(trimmed)
    decoded = base64.b64decode(trimmed)
    if len(decoded) == 32:
        return decoded
    if len(trimmed.encode()) == 32:
        return trimmed.encode()
    raise SystemExit("bad master")


def api(board: str, method: str, path: str, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {board}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:2000]
        raise SystemExit(f"{method} {path} -> {exc.code}: {detail}")


def decrypt_cin() -> tuple[str, str]:
    master = decode_master(Path("/home/ubuntu/.paperclip/instances/default/secrets/master.key").read_text())
    conn = psycopg2.connect("postgres://paperclip:paperclip@127.0.0.1:54329/paperclip")
    cur = conn.cursor()
    cur.execute(
        """
        select s.name, v.material
        from companies c
        join company_secrets s on s.company_id=c.id
        join company_secret_versions v on v.secret_id=s.id and v.version=s.latest_version
        where c.issue_prefix=%s and s.name in (%s,%s)
        """,
        ("CIN", "cursor-api-key", "gh_token"),
    )
    vals = {}
    for name, material in cur.fetchall():
        iv = base64.b64decode(material["iv"])
        tag = base64.b64decode(material["tag"])
        ct = base64.b64decode(material["ciphertext"])
        vals[name] = AESGCM(master).decrypt(iv, ct + tag, None).decode()
    return vals["cursor-api-key"], vals["gh_token"]


def secret_names(rows) -> set[str]:
    if isinstance(rows, dict):
        rows = rows.get("secrets") or rows.get("items") or []
    return {(s.get("name") or s.get("key")) for s in rows if isinstance(s, dict)}


def main() -> int:
    board = read_env(Path("/opt/milepo-oracle/.env"), "PAPERCLIP_API_KEY")
    host_cursor = read_env(Path("/opt/milepo-oracle/.env"), "CURSOR_API_KEY")
    assert board
    cursor_key, gh_token = decrypt_cin()
    assert host_cursor is None or cursor_key != host_cursor, "refusing: CIN cursor key matched host SYN key"

    basic = base64.b64encode((cursor_key + ":").encode()).decode()
    req = urllib.request.Request("https://api.cursor.com/v0/me", headers={"Authorization": f"Basic {basic}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        me = json.loads(resp.read().decode())
    email = me.get("userEmail") or me.get("email")
    assert email == "asafavron@gmail.com", email
    print("cursor_whoami asafavron@gmail.com")

    companies = api(board, "GET", "/api/companies")
    existing = next((c for c in companies if c.get("issuePrefix") == "KIN"), None)
    if existing:
        cid = existing["id"]
        print("company_exists", cid)
    else:
        created = api(board, "POST", "/api/companies", {"name": "Kinwatch", "issuePrefix": "KIN"})
        cid = created["id"]
        print("company_created", cid, created.get("issuePrefix"))
    assert cid not in EXCL
    co = next(c for c in api(board, "GET", "/api/companies") if c["id"] == cid)
    assert co["issuePrefix"] == "KIN", co
    print("assert_prefix_KIN_ok")

    agents = api(board, "GET", f"/api/companies/{cid}/agents")
    for agent in agents:
        agent_id = agent.get("id")
        if agent.get("name") in ("Summarizer", "Reflection Coach") and agent.get("status") != "terminated":
            api(board, "POST", f"/api/agents/{agent_id}/terminate", {})
            print("terminated", agent.get("name"))

    names = secret_names(api(board, "GET", f"/api/companies/{cid}/secrets"))
    if "cursor-api-key" not in names:
        api(board, "POST", f"/api/companies/{cid}/secrets", {"name": "cursor-api-key", "value": cursor_key})
        print("secret_created cursor-api-key")
    else:
        print("secret_exists cursor-api-key")
    if "gh_token" not in names:
        api(board, "POST", f"/api/companies/{cid}/secrets", {"name": "gh_token", "value": gh_token})
        print("secret_created gh_token")
    else:
        print("secret_exists gh_token")

    agents = api(board, "GET", f"/api/companies/{cid}/agents")
    roles = {}
    for agent in agents:
        if agent.get("status") == "terminated":
            continue
        roles[(agent.get("role") or "").lower()] = agent
    if "ceo" not in roles:
        ceo = api(
            board,
            "POST",
            f"/api/companies/{cid}/agents",
            {
                "name": "CEO",
                "role": "ceo",
                "adapterType": "cursor",
                "heartbeatEnabled": False,
                "heartbeatInterval": 0,
                "adapterConfig": {"env": {"CURSOR_API_KEY": "secret_ref:cursor-api-key"}},
            },
        )
        print("created_ceo", ceo.get("id"))
        roles["ceo"] = ceo
    else:
        print("ceo_exists", roles["ceo"]["id"])
    if "cto" not in roles:
        cto = api(
            board,
            "POST",
            f"/api/companies/{cid}/agents",
            {
                "name": "CTO",
                "role": "cto",
                "adapterType": "cursor",
                "heartbeatEnabled": False,
                "heartbeatInterval": 0,
                "adapterConfig": {"env": {"CURSOR_API_KEY": "secret_ref:cursor-api-key"}},
                "reportsTo": roles["ceo"]["id"],
            },
        )
        print("created_cto", cto.get("id"))
    else:
        print("cto_exists", roles["cto"]["id"])
    print("KIN_ID", cid)
    print("phase_d_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
