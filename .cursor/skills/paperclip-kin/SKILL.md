---
name: paperclip-kin
description: Interact with Paperclip company KIN (Kinwatch) — issues, agents, comments, heartbeats.
---

# Paperclip KIN

Use this skill for **board/API work** on Kinwatch. Use `oracle-connection` for SSH/host facts. Both are KIN-only.

**Never** operate on SYN / Maqom (UUID `94bea508-f6a9-44db-b44c-ff6a6974b3e5`).
**Never** operate on CIN / CineTrace AI (UUID `164be67f-99d2-4e4e-8573-e017d3805f8e`).
**Never** operate on PKN / PocketNode Core (UUID `2dfca2d5-4c80-4a9d-b5bb-19b9323c5a20`).
Never `companies[0]`.
Do not commit board tokens. Read `PAPERCLIP_API_KEY` on Oracle from `/opt/milepo-oracle/.env`.

## Resolve company (every session)

```bash
ssh oracle 'KEY=$(grep "^PAPERCLIP_API_KEY=" /opt/milepo-oracle/.env | cut -d= -f2- | tr -d "\r")
curl -sf -H "Authorization: Bearer $KEY" http://127.0.0.1:3100/api/companies \
  | python3 -c "
import json,sys
rows=json.load(sys.stdin)
co=next((c for c in rows if c.get(\"issuePrefix\")==\"KIN\"), None)
assert co, \"KIN company not found\"
assert co[\"id\"]!=\"94bea508-f6a9-44db-b44c-ff6a6974b3e5\"
assert co[\"id\"]!=\"164be67f-99d2-4e4e-8573-e017d3805f8e\"
assert co[\"id\"]!=\"2dfca2d5-4c80-4a9d-b5bb-19b9323c5a20\"
print(co[\"id\"])
"'
```

UI: `https://paperclip.maqom.buzz/KIN/`
API on host: `http://127.0.0.1:3100` with `Authorization: Bearer $PAPERCLIP_API_KEY`.

## Common actions (KIN only)

Prefix every CLI call with `--api-base http://127.0.0.1:3100 --api-key "$PAPERCLIP_API_KEY"` and `-C "$COMPANY_ID"`. Run on Oracle via `ssh oracle`.

```bash
# list
paperclipai issue list -C "$COMPANY_ID" --api-base http://127.0.0.1:3100 --api-key "$KEY" --json
paperclipai agent list -C "$COMPANY_ID" --api-base http://127.0.0.1:3100 --api-key "$KEY" --json

# create issue
paperclipai issue create -C "$COMPANY_ID" --title "..." --description "..." \
  --assignee-agent-id "$AGENT_ID" --api-base http://127.0.0.1:3100 --api-key "$KEY" --json

# one-shot heartbeat
paperclipai heartbeat run --agent-id "$AGENT_ID" --source on_demand --trigger manual \
  --timeout-ms 180000 --api-base http://127.0.0.1:3100 --api-key "$KEY"
```

## Worktrees

```text
/home/ubuntu/.kinwatch/github.env     # GH_TOKEN=...  chmod 600; never commit
/opt/kinwatch                         # main checkout
/opt/kinwatch/worktrees/<slug>        # one worktree per KIN agent
```

Oracle global `gh` is **`insiteu-bot`**. Never `gh auth login` with the KIN PAT.
Feature branches + PRs only. Never push `main` from an agent.

## Isolation checklist

- Company filter: `issuePrefix == "KIN"`
- No SYN issue ids (`SYN-*`)
- No CIN issue ids (`CIN-*`)
- No PKN issue ids (`PKN-*`)
- No `/opt/milepo-app` worktrees
- No `/opt/cinetrace-ai` worktrees
- No `/opt/pocketnode-core` worktrees
