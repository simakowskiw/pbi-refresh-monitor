from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(ValueError):
    pass


def _get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and (value is None or value == ""):
        raise ConfigError(f"Missing required environment variable: {name}")
    if value is None:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class PowerBIConfig:
    tenant_id: str
    client_id: str
    client_secret: str
    scope: str
    api_base: str
    http_timeout_sec: float
    retry_max_attempts: int
    retry_backoff_min_sec: float
    retry_backoff_max_sec: float
    user_agent: str
    log_level: str


def load_config() -> PowerBIConfig:
    return PowerBIConfig(
        tenant_id=_get_env("AZURE_TENANT_ID", required=True),
        client_id=_get_env("AZURE_CLIENT_ID", required=True),
        client_secret=_get_env("AZURE_CLIENT_SECRET", required=True),
        scope=_get_env(
            "POWERBI_SCOPE",
            default="https://analysis.windows.net/powerbi/api/.default",
        ),
        api_base=_get_env(
            "POWERBI_API_BASE",
            default="https://api.powerbi.com/v1.0/myorg",
        ),
        http_timeout_sec=float(_get_env("POWERBI_HTTP_TIMEOUT_SEC", default="30")),
        retry_max_attempts=int(_get_env("POWERBI_RETRY_MAX_ATTEMPTS", default="5")),
        retry_backoff_min_sec=float(
            _get_env("POWERBI_RETRY_BACKOFF_MIN_SEC", default="0.5")
        ),
        retry_backoff_max_sec=float(
            _get_env("POWERBI_RETRY_BACKOFF_MAX_SEC", default="5")
        ),
        user_agent=_get_env(
            "POWERBI_USER_AGENT",
            default="pbi-refresh-monitor/0.1",
        ),
        log_level=_get_env("LOG_LEVEL", default="INFO").upper(),
    )
