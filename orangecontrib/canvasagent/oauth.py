from __future__ import annotations

from dataclasses import dataclass

try:
    import keyring
except Exception:  # pragma: no cover - keyring is optional during bare imports
    keyring = None

from .backend import AuthStatus


@dataclass(frozen=True)
class OAuthSession:
    provider: str
    account: str
    access_token: str


class LocalOAuthGateway:
    """Small keyring-backed boundary for provider-neutral auth state."""

    service_name = "orange3-canvasagent"

    def save_session(self, session: OAuthSession) -> AuthStatus:
        if keyring is None:
            return AuthStatus(False, "keyring is not installed.")
        keyring.set_password(self.service_name, self._key(session.provider, session.account), session.access_token)
        return AuthStatus(True, f"Saved {session.provider} session for {session.account}.")

    def load_session(self, provider: str, account: str) -> OAuthSession | None:
        if keyring is None:
            return None
        token = keyring.get_password(self.service_name, self._key(provider, account))
        if not token:
            return None
        return OAuthSession(provider=provider, account=account, access_token=token)

    def status(self, provider: str, account: str) -> AuthStatus:
        if self.load_session(provider, account):
            return AuthStatus(True, f"{provider} session is available.")
        return AuthStatus(False, f"No {provider} session is stored.")

    def _key(self, provider: str, account: str) -> str:
        return f"{provider}:{account}"

