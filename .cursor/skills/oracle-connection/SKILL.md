---
name: oracle-connection
description: Oracle infrastructure for KIN (Kinwatch) only. Use when investigating Oracle host or Paperclip KIN company.
---

# Oracle Infrastructure Connection (Kinwatch / KIN)

This skill is for the **kinwatch** workspace. Paperclip work is **KIN / Kinwatch only**.

**Never** list, patch, archive, or delete company **SYN / Maqom** (UUID `94bea508-f6a9-44db-b44c-ff6a6974b3e5`).
**Never** list, patch, archive, or delete company **CIN / CineTrace AI** (UUID `164be67f-99d2-4e4e-8573-e017d3805f8e`).
**Never** list, patch, archive, or delete company **PKN / PocketNode Core** (UUID `2dfca2d5-4c80-4a9d-b5bb-19b9323c5a20`).
Never treat `companies[0]` as KIN.

Do not change `/opt/milepo-oracle` deploy defaults. Do not commit board tokens into this repo.

## SSH Connection

- **Host**: `151.145.87.224` (Oracle ARM instance)
- **User**: `ubuntu`
- **SSH Alias**: `oracle`

```bash
ssh oracle
```

## Service Discovery Index

Host services live under `/opt/milepo-oracle`. They are shared infrastructure.

| Service | Port | Purpose |
|---------|------|---------|
| Paperclip | 3100 | AI orchestration; use company KIN only |
| nginx-proxy | 80/443 | Reverse proxy |

## Environment Variables

- **Location**: `/opt/milepo-oracle/.env` (board token `PAPERCLIP_API_KEY`)
- **Paperclip API**: `http://127.0.0.1:3100` (on Oracle)

KIN Cursor and GitHub identities are **not** the host `.env` `CURSOR_API_KEY`. That key is SYN (`asafa.insiteu@gmail.com`). KIN uses Paperclip secret `cursor-api-key` copied from CIN and `~/.kinwatch/github.env` copied from `~/.cinetrace/github.env`.

## Key URLs

- **Paperclip**: `https://paperclip.maqom.buzz/`
- **KIN company UI**: `https://paperclip.maqom.buzz/KIN/`

## Resolve company (every session)

```bash
ssh oracle 'KEY=$(grep "^PAPERCLIP_API_KEY=" /opt/milepo-oracle/.env | cut -d= -f2- | tr -d "\r")
curl -sf -H "Authorization: Bearer $KEY" http://127.0.0.1:3100/api/companies \
  | python3 -c "
import json,sys
rows=json.load(sys.stdin)
co=next((c for c in rows if c.get(\"issuePrefix\")==\"KIN\"), None)
assert co, \"KIN company not found\"
assert co[\"id\"]!=\"94bea508-f6a9-44db-b44c-ff6a6974b3e5\", \"Resolved SYN instead of KIN\"
assert co[\"id\"]!=\"164be67f-99d2-4e4e-8573-e017d3805f8e\", \"Resolved CIN instead of KIN\"
assert co[\"id\"]!=\"2dfca2d5-4c80-4a9d-b5bb-19b9323c5a20\", \"Resolved PKN instead of KIN\"
print(co[\"id\"])
"'
```

## KIN checkout

- Clone: `/opt/kinwatch` with worktrees at `/opt/kinwatch/worktrees/<slug>`
- GitHub PAT: `/home/ubuntu/.kinwatch/github.env` (chmod 600). Never `gh auth login` with it.
- Worktree timer: `kinwatch-worktree-automation.timer` (KIN only).

## Common Commands

### Docker Compose (run from `/opt/milepo-oracle`)

```bash
cd /opt/milepo-oracle
sudo docker compose ps
sudo docker compose logs <service>
```

Use `sudo` for docker and systemctl.

## Notes

- Paperclip is a host systemd service (`paperclip`), not only Docker.
- Do not use `/opt/milepo-app`, `/opt/cinetrace-ai`, or `/opt/pocketnode-core` worktrees.
