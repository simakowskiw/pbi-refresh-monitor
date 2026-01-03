from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import uuid

import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from .config import PowerBIConfig
from .errors import (
    PowerBIAuthError,
    PowerBINotFoundError,
    PowerBIRateLimitError,
    PowerBIRequestError,
    PowerBIRetryableError,
)


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        seconds = float(value)
        return max(0.0, seconds)
    except ValueError:
        pass

    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        delta = (retry_at - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, delta)
    except (TypeError, ValueError):
        return None


class PowerBIClient:
    def __init__(self, config: PowerBIConfig, token_provider):
        self._config = config
        self._token_provider = token_provider
        self._client = httpx.Client(
            base_url=config.api_base.rstrip("/"),
            timeout=config.http_timeout_sec,
            headers={
                "Accept": "application/json",
                "User-Agent": config.user_agent,
            },
        )
        self._exp_wait = wait_exponential_jitter(
            initial=config.retry_backoff_min_sec,
            max=config.retry_backoff_max_sec,
        )
        self._retrying = Retrying(
            retry=retry_if_exception_type(PowerBIRetryableError),
            stop=stop_after_attempt(config.retry_max_attempts),
            wait=self._retry_wait,
            reraise=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PowerBIClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _retry_wait(self, retry_state) -> float:
        exc = retry_state.outcome.exception()
        if isinstance(exc, PowerBIRetryableError) and exc.retry_after_sec is not None:
            return exc.retry_after_sec
        return self._exp_wait(retry_state)

    def _request_once(self, method: str, path: str, params: dict | None = None):
        access_token = self._token_provider.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "x-ms-client-request-id": str(uuid.uuid4()),
        }
        response = self._client.request(method, path, params=params, headers=headers)

        if response.status_code in (401, 403):
            raise PowerBIAuthError(
                f"Unauthorized response {response.status_code}: {response.text}"
            )
        if response.status_code == 404:
            raise PowerBINotFoundError(f"Not found: {response.text}")
        if response.status_code == 429:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            raise PowerBIRateLimitError("Rate limited", retry_after_sec=retry_after)
        if 500 <= response.status_code <= 599:
            raise PowerBIRetryableError(
                f"Server error {response.status_code}: {response.text}"
            )
        if response.status_code >= 400:
            raise PowerBIRequestError(
                f"Request failed {response.status_code}: {response.text}"
            )

        if response.status_code == 204:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise PowerBIRequestError("Invalid JSON response") from exc

    def _request(self, method: str, path: str, params: dict | None = None):
        for attempt in self._retrying:
            with attempt:
                return self._request_once(method, path, params=params)
        return None

    def list_workspaces(self) -> list[dict]:
        data = self._request("GET", "/groups")
        if not data:
            return []
        return data.get("value", [])

    def list_datasets(self, workspace_id: str) -> list[dict]:
        data = self._request("GET", f"/groups/{workspace_id}/datasets")
        if not data:
            return []
        return data.get("value", [])

    def get_refresh_history(
        self,
        workspace_id: str,
        dataset_id: str,
        top: int | None = None,
    ) -> list[dict]:
        params = {"$top": top} if top is not None else None
        data = self._request(
            "GET",
            f"/groups/{workspace_id}/datasets/{dataset_id}/refreshes",
            params=params,
        )
        if not data:
            return []
        return data.get("value", [])
