#!/bin/bash
# KIN-only: one CEO heartbeat then one CTO heartbeat. Never SYN. Never CIN. Never PKN.
set -euo pipefail
KEY=$(grep "^PAPERCLIP_API_KEY=" /opt/milepo-oracle/.env | cut -d= -f2- | tr -d "\r")
KIN=$(curl -sf -H "Authorization: Bearer $KEY" http://127.0.0.1:3100/api/companies | python3 -c "
import json,sys
rows=json.load(sys.stdin)
kin=next((c for c in rows if c.get('issuePrefix')=='KIN'), None)
assert kin, 'KIN company not found'
assert kin['id']!='94bea508-f6a9-44db-b44c-ff6a6974b3e5'
assert kin['id']!='164be67f-99d2-4e4e-8573-e017d3805f8e'
assert kin['id']!='2dfca2d5-4c80-4a9d-b5bb-19b9323c5a20'
print(kin['id'])
")
CEO=$(curl -sf -H "Authorization: Bearer $KEY" "http://127.0.0.1:3100/api/companies/$KIN/agents" | python3 -c "
import json,sys
rows=json.load(sys.stdin)
ceo=next((a for a in rows if (a.get('role') or '').lower()=='ceo'), None)
assert ceo
print(ceo['id'])
")
CTO=$(curl -sf -H "Authorization: Bearer $KEY" "http://127.0.0.1:3100/api/companies/$KIN/agents" | python3 -c "
import json,sys
rows=json.load(sys.stdin)
cto=next((a for a in rows if (a.get('role') or '').lower()=='cto'), None)
assert cto
print(cto['id'])
")
API=(--api-base http://127.0.0.1:3100 --api-key "$KEY")
paperclipai heartbeat run --agent-id "$CEO" --source timer --trigger system --timeout-ms 180000 "${API[@]}"
paperclipai heartbeat run --agent-id "$CTO" --source timer --trigger system --timeout-ms 180000 "${API[@]}"
