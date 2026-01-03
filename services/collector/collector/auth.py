import msal

from .config import PowerBIConfig
from .errors import PowerBIAuthError


class PowerBITokenProvider:
    def __init__(self, config: PowerBIConfig):
        self._authority = f"https://login.microsoftonline.com/{config.tenant_id}"
        self._client = msal.ConfidentialClientApplication(
            client_id=config.client_id,
            authority=self._authority,
            client_credential=config.client_secret,
        )
        self._scopes = [config.scope]

    def get_access_token(self) -> str:
        result = self._client.acquire_token_silent(self._scopes, account=None)
        if not result:
            result = self._client.acquire_token_for_client(scopes=self._scopes)

        token = result.get("access_token") if isinstance(result, dict) else None
        if not token:
            error = result.get("error") if isinstance(result, dict) else "unknown_error"
            description = result.get("error_description") if isinstance(result, dict) else ""
            raise PowerBIAuthError(f"Token acquisition failed: {error} {description}")

        return token
