"""One-way Ring account linking (Ring-driven). Not AgentCore Gateway 3LO."""

from __future__ import annotations

from typing import Any

import httpx

from kinwatch.ring.hmac import verify_linking_nonce
from kinwatch.settings import Settings


class LinkingError(ValueError):
    pass


class AccountLinking:
    def __init__(self, settings: Settings, http: httpx.Client | None = None):
        self.settings = settings
        self._http = http or httpx.Client(timeout=20.0)

    def validate_nonce(self, timestamp_ms: str, account_id: str, nonce: str) -> None:
        if not verify_linking_nonce(self.settings.ring_hmac_key, timestamp_ms, account_id, nonce):
            raise LinkingError("nonce mismatch")

    def exchange_token(self, code: str, redirect_uri: str, code_verifier: str | None = None) -> dict[str, Any]:
        if self.settings.use_fixtures:
            return {"access_token": "fixture-access", "refresh_token": "fixture-refresh", "token_type": "Bearer"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.settings.ring_client_id,
            "client_secret": self.settings.ring_client_secret,
            "redirect_uri": redirect_uri,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        resp = self._http.post(self.settings.ring_oauth_token_url, data=data)
        resp.raise_for_status()
        return resp.json()

    def complete_integration(self, access_token: str, account_identifier: str) -> dict[str, Any]:
        if self.settings.use_fixtures:
            return {"status": "completed", "account_identifier": account_identifier}
        url = f"{self.settings.ring_api_base.rstrip('/')}/v1/accounts/me/app-integrations"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/vnd.api+json"}
        awaiting = {
            "data": {
                "type": "app-integrations",
                "attributes": {"status": "awaiting", "account_identifier": account_identifier},
            }
        }
        self._http.post(url, headers=headers, json=awaiting)
        completed = {
            "data": {
                "type": "app-integrations",
                "attributes": {"status": "completed", "account_identifier": account_identifier},
            }
        }
        resp = self._http.patch(url, headers=headers, json=completed)
        resp.raise_for_status()
        return {"status": "completed", "account_identifier": account_identifier}

    def receive_ring_token_exchange(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Token Exchange URL: Ring POSTs an authorization code to the partner backend."""
        code = str(payload.get("code") or "")
        if not code and not self.settings.use_fixtures:
            raise LinkingError("missing authorization code")
        tokens = self.exchange_token(
            code=code or "fixture",
            redirect_uri=payload.get("redirect_uri") or self.settings.public_base_url,
            code_verifier=payload.get("code_verifier"),
        )
        return {"ok": True, "token_type": tokens.get("token_type", "Bearer")}
