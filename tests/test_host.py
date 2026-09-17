def test_health_agentcore_listen_contract(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["mcp_protocol"] == "2025-11-25"
    assert body["listen"].startswith("0.0.0.0:")
    assert body["ok"] is True


def test_mcp_get_documents_streamable_http(client):
    res = client.get("/mcp")
    assert res.status_code == 200
    assert "2025-11-25" in res.text
