def test_companion_is_html_and_wcag_basics(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert "lang=\"en\"" in html
    assert "Skip to ask" in html
    assert "prefers-reduced-motion" in html
    assert "Delete household data" in html
    assert "cannot lock" in html.lower()
    assert "ava1.ring" not in html


def test_linking_confirmation_lists_device_names(client):
    res = client.get("/linking/start")
    assert res.status_code == 200
    names = [d["name"] for d in res.json()["devices"]["devices"]]
    assert "Mom's front door" in names
    assert all("ava1.ring" not in n for n in names)


def test_data_deletion(client):
    client.post("/demo/inject")
    gone = client.delete("/api/data")
    assert gone.json()["deleted"] is True
    brief = client.get("/api/brief").json()["briefing"]
    assert "watching" in brief.lower() or "nothing" in brief.lower()
