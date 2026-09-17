# Kinwatch

The remote family member who never sleeps at the door.

Kinwatch is a caretaking copilot for a **Ring** household: doorbell, cameras, contact sensors, and chime fused into one incident, briefed in plain language to the person at home and the adult child who is away. It is **not** a generic MCP wrapper and it does **not** lock or unlock doors.

## Judge run (through 20 Nov 2026)

Submit freeze: **23 Oct 2026 12:00 PT**. Keep this repo and a running demo available through judging (**9–20 Nov 2026**).

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -e ".[dev]"
cp .env.example .env
uvicorn kinwatch.app:app --host 0.0.0.0 --port 8000
```

Open:

- Companion (simulated Alexa+ host): http://127.0.0.1:8000/
- Health: http://127.0.0.1:8000/health
- MCP Streamable HTTP (protocol `2025-11-25`): `POST http://127.0.0.1:8000/mcp`
- Ring webhook: `POST http://127.0.0.1:8000/webhooks/ring`
- Demo injector (films the 3-minute incident without waiting for a doorbell): `POST http://127.0.0.1:8000/demo/inject`

Default mode uses **Playground fixtures** (`KINWATCH_USE_FIXTURES=true`). No Ring token required to see the product. With a live Partner API token, set `KINWATCH_USE_FIXTURES=false` and `RING_ACCESS_TOKEN`.

If a hosted demo is gated, judge credentials will be listed here. Until then, local fixtures are the official path.

## What it does

1. **Fused doorstep graph** — doorbell button, camera motion, and contact-sensor open become one incident.
2. **Live WHEP** — companion embeds Ring live view (fixture SDP in demo mode).
3. **Vision** — Bedrock (or fixture classifier) on a privacy-zone-cropped snapshot: person / package / animal / unknown.
4. **Household policy** — quiet hours, door-open escalation, unanswered doorbell → live view + family brief.
5. **Memory** — file store or DynamoDB: incidents, last door state, family-labeled visitors. Sensors have no Event History; memory is the product.
6. **MCP Apps** — visitor card, timeline, live-view widgets (`ui://kinwatch/...`).
7. **Voice companion** — speech in/out against the **same** MCP tool layer. Typed chat is the fallback.
8. **Chime playback** — the only partner write: “I’m looking / I’m coming.”
9. **One-way Ring account linking** — token exchange URL, nonce HMAC (URL-safe Base64), `app-integrations` completed.
10. **Strands + AgentCore + Bedrock** — agent loop in-repo; container listens `0.0.0.0:8000` for AgentCore Runtime.

## What it does not do

- No `set_lock_state`. Partner API cannot actuate locks.
- No Gateway 3LO against Ring. Linking is Ring one-way account linking.
- Webhooks acknowledge with **HTTP 200** (not 202) after persist, within 5 seconds.
- Alexa+ MCP version is **2025-11-25**, not 2026-07-28.

## Tracks

Dual-enter **Ring**, **Alexa+**, and **AWS Builder**. Open Source mini = this public MIT repo.

Product feedback: [`FEEDBACK.md`](FEEDBACK.md). Friction logs: [`FRICTION.md`](FRICTION.md). Feature requests: [`FEATURE_REQUESTS.md`](FEATURE_REQUESTS.md). Video script: [`VIDEO.md`](VIDEO.md). Human unblockers: [`HUMAN.md`](HUMAN.md).

## Paperclip / Oracle

Oracle and Paperclip are allowed **only** for company **KIN / Kinwatch**.
Use `.cursor/skills/oracle-connection` for SSH/host facts and `.cursor/skills/paperclip-kin` for board work.
Resolve the company at runtime with `issuePrefix == "KIN"`. Never use `companies[0]`.
Board tokens stay on the Oracle host; do not commit them here.

## License

MIT. GitHub About should show this `LICENSE` file.
