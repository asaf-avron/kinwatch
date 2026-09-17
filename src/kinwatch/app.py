from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from kinwatch import MCP_PROTOCOL_VERSION
from kinwatch.companion import companion_html, speak
from kinwatch.mcp_server import handle_mcp, new_session_id
from kinwatch.ring.linking import AccountLinking, LinkingError
from kinwatch.ring.webhooks import WebhookRejected, verify_and_parse
from kinwatch.runtime import KinwatchRuntime
from kinwatch.settings import Settings
from kinwatch.strands_agent import run_strands_brief

FORBIDDEN_LOCK_PATHS = ("/lock", "/unlock", "/set_lock_state")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = Settings()
    app.state.runtime = KinwatchRuntime(app.state.settings)
    app.state.linking = AccountLinking(app.state.settings)
    yield


app = FastAPI(
    title="Kinwatch",
    version="0.1.0",
    description="Ring + Alexa+ caretaking copilot. MCP 2025-11-25 Streamable HTTP.",
    lifespan=lifespan,
)


@app.middleware("http")
async def reject_lock_routes(request: Request, call_next):
    if any(request.url.path.startswith(p) for p in FORBIDDEN_LOCK_PATHS):
        return JSONResponse({"error": "no lock actuation"}, status_code=404)
    return await call_next(request)


@app.get("/health")
def health(request: Request) -> dict:
    runtime: KinwatchRuntime = request.app.state.runtime
    return {
        "ok": True,
        "mcp_protocol": MCP_PROTOCOL_VERSION,
        "fixtures": runtime.settings.use_fixtures,
        "listen": f"{runtime.settings.host}:{runtime.settings.port}",
    }


@app.get("/", response_class=HTMLResponse)
def companion() -> str:
    return companion_html()


@app.get("/api/devices")
def devices(request: Request) -> dict:
    return request.app.state.runtime.call("list_devices")


@app.get("/api/brief")
def brief(request: Request) -> dict:
    return request.app.state.runtime.call("brief_household")


@app.post("/api/utterance")
def utterance(request: Request, body: dict) -> dict:
    runtime: KinwatchRuntime = request.app.state.runtime
    text = str((body or {}).get("text") or "")
    result = run_strands_brief(runtime, text)
    speech = speak(str(result.get("text") or ""), runtime.settings)
    result["speech"] = speech
    return result


@app.delete("/api/data")
def delete_data(request: Request) -> dict:
    return request.app.state.runtime.call("delete_household_data")


@app.get("/widgets/{kind}", response_class=HTMLResponse)
def widget(kind: str, request: Request) -> str:
    return request.app.state.runtime.widget(kind)


@app.post("/demo/inject")
def demo_inject(request: Request) -> dict:
    return request.app.state.runtime.inject_demo()


@app.post("/webhooks/ring")
async def ring_webhook(
    request: Request,
    x_signature: str = Header(default="", alias="X-Signature"),
) -> JSONResponse:
    raw = await request.body()
    settings: Settings = request.app.state.settings
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
        event = verify_and_parse(settings.ring_hmac_key, raw, x_signature, payload)
    except (json.JSONDecodeError, WebhookRejected) as exc:
        return JSONResponse({"error": str(exc)}, status_code=401)
    # Persist first, then 200 — Ring requires 200 in 5s, not 202.
    result = request.app.state.runtime.ingest_event_payload(payload)
    result["event_type"] = event.event_type
    return JSONResponse(result, status_code=200)


@app.post("/oauth/token")
async def ring_token_exchange(request: Request) -> dict:
    payload = await request.json()
    return request.app.state.linking.receive_ring_token_exchange(payload)


@app.get("/linking/start")
def linking_start(request: Request, time: str = "", account_id: str = "", nonce: str = "") -> dict:
    linking: AccountLinking = request.app.state.linking
    try:
        if time and account_id and nonce:
            linking.validate_nonce(time, account_id, nonce)
        return {
            "ok": True,
            "message": "Sign in to Kinwatch, then we will confirm the Ring link. Email OTP is not required to finish linking.",
            "devices": request.app.state.runtime.call("list_devices"),
        }
    except LinkingError as exc:
        return {"ok": False, "error": str(exc)}


@app.post("/linking/complete")
async def linking_complete(request: Request) -> dict:
    body = await request.json()
    linking: AccountLinking = request.app.state.linking
    return linking.complete_integration(body.get("access_token") or "fixture", body.get("account_identifier") or "family")


@app.post("/mcp")
@app.post("/mcp/")
async def mcp_endpoint(
    request: Request,
    mcp_session_id: str | None = Header(default=None, alias="Mcp-Session-Id"),
) -> Response:
    raw = await request.body()
    try:
        message = json.loads(raw.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}, status_code=400)
    session = mcp_session_id or new_session_id()
    result = handle_mcp(request.app.state.runtime, message, session)
    return JSONResponse(
        result,
        headers={
            "Mcp-Session-Id": session,
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        },
    )


@app.get("/mcp")
def mcp_get() -> PlainTextResponse:
    return PlainTextResponse(
        f"Kinwatch MCP Streamable HTTP {MCP_PROTOCOL_VERSION}. POST JSON-RPC to this path.",
        headers={"MCP-Protocol-Version": MCP_PROTOCOL_VERSION},
    )


def main() -> None:
    import uvicorn

    settings = Settings()
    uvicorn.run("kinwatch.app:app", host=settings.host, port=settings.port, factory=False)


if __name__ == "__main__":
    main()
