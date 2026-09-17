import hashlib
import hmac

from kinwatch.ring.hmac import linking_nonce, verify_linking_nonce, verify_webhook_signature


def test_webhook_hmac_hex_sha256_prefix():
    body = b'{"meta":{"request_id":"1"}}'
    key = "fixture-hmac-key"
    digest = hmac.new(key.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(key, body, f"sha256={digest}")
    assert not verify_webhook_signature(key, body, f"sha256={digest[:-1]}0")


def test_linking_nonce_urlsafe_not_hex():
    key = "fixture-hmac-key"
    nonce = linking_nonce(key, "1710000000000", "ava1.ring.account.MOM")
    assert "+" not in nonce and "/" not in nonce and "=" not in nonce
    hex_digest = hmac.new(key.encode(), b"1710000000000:ava1.ring.account.MOM", hashlib.sha256).hexdigest()
    assert nonce != hex_digest
    assert verify_linking_nonce(key, "1710000000000", "ava1.ring.account.MOM", nonce)
