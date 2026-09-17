# Product feedback (per SDK / API)

Required Devpost fields. One block per tool.

## Ring Partner API (amazonvision)

- **Used for:** Device discovery by household name, status, capabilities, configurations (privacy zones), snapshots, camera Event History, WHEP live view, HMAC webhooks, chime playback, one-way account linking.
- **Worked:** JSON:API device model, `?include=status,capabilities,configurations`, documented HMAC (`X-Signature: sha256=`), persist-then-200 webhooks, WHEP 201 + Location.
- **Needs work:** Playground token TTL; Event History missing for sensors; HMAC vs nonce encoding split; chime `audio_ref` provisioning is outside the device API.
- **Onboarding zero-to-hello-world:** Docs are complete but long. A “fixture household in 5 minutes” path is what we shipped locally.
- **Build again?** Yes — the API is the physical proof the video needs. Not if lock actuation is required; that API does not exist.

## Ring webhooks

- **Used for:** `button_press`, motion, `device_online/offline`, contact-style sensor events, `device_removed`, idempotency via `meta.request_id`.
- **Worked:** Raw-body HMAC, 200-in-5s contract is implementable if you persist first.
- **Needs work:** Returning 202 is a common REST habit and fails Ring’s contract.
- **Onboarding:** Signature sample in docs is correct if you do not re-serialize JSON.
- **Build again?** Yes.

## Alexa+ MCP (2025-11-25 Streamable HTTP)

- **Used for:** Self-hosted MCP tools + MCP Apps widgets; simulated Alexa+ host in this repo.
- **Worked:** Stateless Streamable HTTP on `/mcp` with `Mcp-Session-Id` accepted.
- **Needs work:** Confirm when 2026-07-28 is allowed; US-only toolkit blocked a real add-on as the submit demo.
- **Onboarding:** Spec is enough; Preview access is the gate.
- **Build again?** Yes for the simulated path. Real add-on only if Preview is actually open.

## MCP Apps

- **Used for:** Visitor card, incident timeline, inline live view (`ui://kinwatch/...`).
- **Worked:** Resource HTML is straightforward.
- **Needs work:** Few clients render `ui://`; we render in the companion so judges see it.
- **Onboarding:** Sparse compared to tools/list.
- **Build again?** Yes — this is the Alexa+ creative bar.

## Amazon Bedrock (vision + optional speech)

- **Used for:** Arrival classification on privacy-zone-cropped snapshots; companion speech via Nova/Polly when AWS is configured.
- **Worked:** Image-to-label with a strict JSON schema is a good fit for caretaking language.
- **Needs work:** Cold-start latency vs the &lt;500 ms Alexa+ round-trip story; we cache last classification on the incident.
- **Onboarding:** IAM + model access is slower than Playground.
- **Build again?** Yes.

## Amazon Bedrock AgentCore Runtime

- **Used for:** Container contract: `0.0.0.0:8000`, `/mcp`, extra FastAPI routes for webhooks/companion.
- **Worked:** One process can serve MCP and HTTP if the platform forwards all paths.
- **Needs work:** Samples imply MCP-only; extra routes are a guess until the first deploy.
- **Onboarding:** Dockerfile in this repo is the hello-world.
- **Build again?** Yes, with App Runner documented as fallback.

## Strands (Agents)

- **Used for:** Agentic loop over the same Kinwatch tools (policy → snapshot → vision → chime → brief).
- **Worked:** Optional extra; local policy engine runs when Strands is not installed.
- **Needs work:** Extra is heavy for a fixture demo.
- **Onboarding:** Import-optional keeps `pip install -e .` light.
- **Build again?** Yes for the AWS Builder paragraph.

## FastAPI + FastMCP / MCP Python SDK

- **Used for:** HTTP companion, webhooks, Streamable HTTP MCP.
- **Worked:** One app, one tool layer.
- **Needs work:** FastMCP mount vs a hand-written `/mcp` JSON-RPC — we implement `/mcp` explicitly so AgentCore session headers are not optional.
- **Onboarding:** Fine.
- **Build again?** Yes.
