# Friction logs

Official-rules schema. Amazon engineering can read these. Start on commit 1; update when a surface actually hurts.

Each entry:

- **Task attempted**
- **Steps**
- **Expected vs actual**
- **Severity** (blocker / major / minor)
- **Workaround**
- **Actionable suggestion**

---

## Playground tokens expire too fast for a filmed demo

- **Task attempted:** Keep a Playground Bearer token alive through a 3-minute video plus judge “Run.”
- **Steps:** Request Playground token → configure `RING_ACCESS_TOKEN` → film companion live view.
- **Expected vs actual:** Expected a token that lasts a recording session. Actual: short-lived tokens force fixture mode mid-demo.
- **Severity:** major
- **Workaround:** Fixture Playground (`KINWATCH_USE_FIXTURES=true`) is the default submit path; live token is optional B-roll.
- **Actionable suggestion:** Issue Playground tokens with a 24-hour TTL and a documented refresh endpoint that does not require re-clicking the portal.

## One-way account linking vs partner-initiated OAuth

- **Task attempted:** Link a Ring household from a partner app the way Alexa+ Gateway 3LO tutorials describe.
- **Steps:** Read Ring linking docs; compare to AgentCore Gateway 3LO samples.
- **Expected vs actual:** Expected a partner-initiated code+PKCE start. Actual: Ring-driven one-way linking, invitation-only partner initiation, nonce is URL-safe Base64 while webhooks are `sha256=` hex.
- **Severity:** major
- **Workaround:** Implement Ring’s one-way flow (`POST /oauth/token` exchange URL, nonce HMAC, `POST` then `PATCH /v1/accounts/me/app-integrations`). Do not pretend Gateway 3LO talks to Ring.
- **Actionable suggestion:** Put a single sequence diagram at the top of the linking guide titled “Ring initiates; partner does not.” Call out the two HMAC encodings in the first code sample.

## Webhook HMAC encoding mixed with nonce encoding

- **Task attempted:** Verify `X-Signature` and account-link nonce with one helper.
- **Steps:** HMAC-SHA256 with the portal HMAC key on webhook raw body and on `{timestamp}:{account_id}`.
- **Expected vs actual:** Same key, two encodings. Mixing them fails every check with a payload that “looks right.”
- **Severity:** major
- **Workaround:** `verify_webhook_signature` uses hex; `verify_linking_nonce` uses URL-safe Base64 without padding. Tests lock both.
- **Actionable suggestion:** Ship a one-page “same key, two encodings” snippet in both Notifications and Account Linking.

## WHEP is SDP, not a video URL

- **Task attempted:** Drop a `<video src>` on a live Ring camera.
- **Steps:** `POST /v1/devices/{id}/media/streaming/whep/sessions` with `Content-Type: application/sdp`.
- **Expected vs actual:** 201 + SDP answer + `Location` session URL. There is no progressive MP4.
- **Severity:** minor
- **Workaround:** Companion uses WebRTC; fixtures return a canned SDP so the widget still renders without a camera.
- **Actionable suggestion:** Provide a Playground “canned WHEP” session that browsers can complete without a physical device.

## AgentCore Runtime extra routes and `Mcp-Session-Id`

- **Task attempted:** Serve FastAPI webhooks + companion **and** `/mcp` on AgentCore Runtime.
- **Steps:** Bind `0.0.0.0:8000`, mount Streamable HTTP at `/mcp`, accept `Mcp-Session-Id` even when stateless.
- **Expected vs actual:** Runtime samples assume a single MCP ASGI app. Extra routes work if the platform forwards all paths; that is not obvious from the first page.
- **Severity:** minor
- **Workaround:** One FastAPI app: `/`, `/webhooks/ring`, `/mcp`. Document App Runner as the fallback if Runtime strips non-MCP paths.
- **Actionable suggestion:** Official sample: FastAPI app with `/mcp` plus health/webhook routes on AgentCore Runtime.

## MCP Apps widgets vs tools/list-only clients

- **Task attempted:** Show a visitor card inside an Alexa+ conversation.
- **Steps:** Advertise `ui://kinwatch/visitor` resources; simulated host renders HTML; a tools/list client ignores them.
- **Expected vs actual:** Creative bar wants MCP Apps. Many MCP inspectors never render `ui://`.
- **Severity:** minor
- **Workaround:** Companion always renders the same widgets the MCP resources return, so the video is not hostage to a raw inspector.
- **Actionable suggestion:** Alexa+ simulator should render MCP App HTML the way the companion does.

## Sensors have no Event History

- **Task attempted:** Ask “was the door open at 2:11?” from Ring Event History on a contact sensor.
- **Steps:** `GET /v1/history/devices/{id}/events` for the sensor.
- **Expected vs actual:** Event History is camera/doorbell scoped. Contact sensors do not give a DVR of opens.
- **Severity:** major (product-shaping)
- **Workaround:** Persist sensor webhooks ourselves. Household memory **is** the history.
- **Actionable suggestion:** Offer Event History for contact sensors, even if only last-N opens with no video.

## HMAC key is issued once in the portal

- **Task attempted:** Rotate webhook signing key from the Partner API.
- **Steps:** Look for a rotate endpoint.
- **Expected vs actual:** HMAC key is portal-issued; webhook URL is not API-changeable.
- **Severity:** minor
- **Workaround:** Store `RING_HMAC_KEY` in env; human pastes once (`HUMAN.md`).
- **Actionable suggestion:** API-side HMAC rotate + webhook URL update for staging vs production.
