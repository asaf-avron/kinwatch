from kinwatch.ring.linking import AccountLinking
from kinwatch.ring.hmac import linking_nonce
from kinwatch.settings import Settings


def test_nonce_gate_then_complete(tmp_path, monkeypatch):
    monkeypatch.setenv("KINWATCH_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("KINWATCH_USE_FIXTURES", "true")
    monkeypatch.setenv("RING_HMAC_KEY", "k")
    settings = Settings()
    linking = AccountLinking(settings)
    nonce = linking_nonce("k", "1", "acct")
    linking.validate_nonce("1", "acct", nonce)
    done = linking.complete_integration("fixture", "family")
    assert done["status"] == "completed"


def test_token_exchange_url_fixture():
    settings = Settings()
    linking = AccountLinking(settings)
    out = linking.receive_ring_token_exchange({"code": "abc"})
    assert out["ok"] is True
