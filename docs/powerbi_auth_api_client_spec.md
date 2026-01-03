# Power BI Auth + API Client Spec (Draft)

## Purpose
Define a production-style authentication flow and API client behavior for the Power BI REST API.
This spec is implementation-agnostic and will guide the collector service.

## Auth flow (recommended)
Use Azure AD application (client credentials) flow for service-to-service access.

- Library: `msal` (Python)
- Authority: `https://login.microsoftonline.com/{AZURE_TENANT_ID}`
- Scope: `https://analysis.windows.net/powerbi/api/.default`

### Required permissions (application)
Grant only what the collector needs. Start with:
- Power BI Service: dataset read permissions for refresh history
- Workspace/group read permissions to enumerate workspaces

If you need full tenant coverage, you may need a tenant-wide permission (review in Azure AD).

## Environment variables (local/dev)
These are read from `.env` for local development. Do not commit `.env`.

- `AZURE_TENANT_ID`
- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `POWERBI_SCOPE` (default: `https://analysis.windows.net/powerbi/api/.default`)
- `POWERBI_API_BASE` (default: `https://api.powerbi.com/v1.0/myorg`)
- `POWERBI_HTTP_TIMEOUT_SEC` (default: `30`)
- `POWERBI_RETRY_MAX_ATTEMPTS` (default: `5`)
- `POWERBI_RETRY_BACKOFF_MIN_SEC` (default: `0.5`)
- `POWERBI_RETRY_BACKOFF_MAX_SEC` (default: `5`)
- `POWERBI_USER_AGENT` (default: `pbi-refresh-monitor/0.1`)
- `LOG_LEVEL` (default: `INFO`)

## Token acquisition
- Use `msal.ConfidentialClientApplication` with an in-memory token cache.
- Request a token on startup; refresh when token is near expiry (e.g., within 2 minutes).
- Never log access tokens or client secrets.

## API client responsibilities

### Core endpoints
- List workspaces: `GET /groups`
- List datasets in a workspace: `GET /groups/{group_id}/datasets`
- Refresh history: `GET /groups/{group_id}/datasets/{dataset_id}/refreshes`

### Request headers
- `Authorization: Bearer <token>`
- `Accept: application/json`
- `User-Agent: pbi-refresh-monitor/1.0`
- `x-ms-client-request-id: <uuid>` (for correlation)

### Query parameters
- Support `$top` and `$skip` for paging if the API supports it.
- Use a configurable history window (e.g., `refresh_history_days`).

### Error handling
- 401/403: treat as auth/permission errors; do not retry automatically.
- 404: treat as missing workspace/dataset; log at info and skip.
- 429: retry with backoff; respect `Retry-After` when present.
- 5xx: retry with exponential backoff and jitter.

### Retries
- Use `tenacity` with bounded retries (e.g., 3-5 attempts).
- Retry only for transient errors (429, 5xx, network timeouts).

## Normalization rules
The collector normalizes API responses into `RefreshEventV1`.

- `status`: map Power BI status values to the schema enum.
- `start_time`, `end_time`: parse as UTC RFC 3339.
- `duration_sec`: compute when `end_time` is present.
- `error_message`: pass through error details from API when present.

## Logging & observability
- Log request ID, workspace/dataset IDs, and status.
- Do not log tokens or secrets.
- Include timing metrics for API calls and token refreshes.

## Security notes
- `.env` is for local only and must be in `.gitignore`.
- Production should use a secret manager or environment injection.
