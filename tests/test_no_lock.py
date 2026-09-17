def test_no_lock_tool(client):
    res = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "set_lock_state", "arguments": {"locked": True}}},
    )
    assert res.json()["result"]["isError"] is True
    assert "lock" in res.json()["result"]["structuredContent"]["error"].lower()


def test_lock_http_404(client):
    assert client.post("/set_lock_state").status_code == 404
    assert client.post("/lock").status_code == 404
