from kinwatch import MCP_PROTOCOL_VERSION


def test_initialize_protocol_and_session_header(client):
    res = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": MCP_PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "test", "version": "0"}}},
        headers={"Mcp-Session-Id": "session-kinwatch-1"},
    )
    assert res.status_code == 200
    assert res.headers.get("Mcp-Session-Id") == "session-kinwatch-1"
    assert res.headers.get("MCP-Protocol-Version") == MCP_PROTOCOL_VERSION
    assert res.json()["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION


def test_tools_list_has_ring_surface_not_lock(client):
    res = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = {t["name"] for t in res.json()["result"]["tools"]}
    assert "list_devices" in names
    assert "play_chime" in names
    assert "get_live_view" in names
    assert "set_lock_state" not in names


def test_tools_call_list_devices_uses_names(client):
    res = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "list_devices", "arguments": {}}},
    )
    payload = res.json()["result"]["structuredContent"]
    names = [d["name"] for d in payload["devices"]]
    assert "Mom's front door" in names
    assert all("ava1.ring" not in n for n in names)


def test_mcp_apps_resources(client):
    listed = client.post("/mcp", json={"jsonrpc": "2.0", "id": 4, "method": "resources/list"})
    uris = {r["uri"] for r in listed.json()["result"]["resources"]}
    assert "ui://kinwatch/visitor" in uris
    assert "ui://kinwatch/timeline" in uris
    assert "ui://kinwatch/live-view" in uris
    read = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 5, "method": "resources/read", "params": {"uri": "ui://kinwatch/timeline"}},
    )
    html = read.json()["result"]["contents"][0]["text"]
    assert "Overnight" in html or "overnight" in html.lower() or "door" in html.lower()
