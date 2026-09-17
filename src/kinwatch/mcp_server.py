"""MCP 2025-11-25 Streamable HTTP JSON-RPC at POST /mcp. Accepts Mcp-Session-Id."""

from __future__ import annotations

import uuid
from typing import Any

from kinwatch import MCP_PROTOCOL_VERSION
from kinwatch.runtime import KinwatchRuntime
from kinwatch.widgets import WIDGETS

SERVER_INFO = {"name": "kinwatch", "version": "0.1.0"}


def handle_mcp(runtime: KinwatchRuntime, message: dict[str, Any], session_id: str | None) -> dict[str, Any]:
    method = message.get("method")
    req_id = message.get("id")
    params = message.get("params") or {}
    if method == "initialize":
        return _ok(
            req_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}, "resources": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
                "instructions": "Kinwatch household caretaking copilot. Devices by name. No lock actuation.",
            },
            session_id,
        )
    if method == "notifications/initialized":
        return {"jsonrpc": "2.0", "result": None}
    if method == "ping":
        return _ok(req_id, {}, session_id)
    if method == "tools/list":
        tools = []
        for spec in runtime.tools():
            tools.append(
                {
                    "name": spec["name"],
                    "description": spec["description"],
                    "inputSchema": {"type": "object", "additionalProperties": True},
                }
            )
        return _ok(req_id, {"tools": tools}, session_id)
    if method == "tools/call":
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        result = runtime.call(name, arguments)
        is_error = bool(result.get("error"))
        return _ok(
            req_id,
            {
                "content": [{"type": "text", "text": _as_text(result)}],
                "structuredContent": result,
                "isError": is_error,
            },
            session_id,
        )
    if method == "resources/list":
        resources = [
            {"uri": meta["uri"], "name": meta["name"], "mimeType": meta["mimeType"]}
            for meta in WIDGETS.values()
        ]
        return _ok(req_id, {"resources": resources}, session_id)
    if method == "resources/read":
        uri = str(params.get("uri") or "")
        kind = uri.rsplit("/", 1)[-1]
        html = runtime.widget(kind)
        return _ok(
            req_id,
            {"contents": [{"uri": uri, "mimeType": "text/html;profile=mcp-app", "text": html}]},
            session_id,
        )
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def new_session_id() -> str:
    return str(uuid.uuid4())


def _ok(req_id: Any, result: dict[str, Any], session_id: str | None) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result, "sessionId": session_id}


def _as_text(result: dict[str, Any]) -> str:
    import json

    return json.dumps(result, default=str)
