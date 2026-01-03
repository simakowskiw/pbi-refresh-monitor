from __future__ import annotations

from datetime import datetime, timezone
import uuid


_REFRESH_EVENT_NAMESPACE = uuid.NAMESPACE_URL


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_rfc3339(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_event_id(
    workspace_id: str,
    dataset_id: str,
    refresh_id: str,
    status: str,
) -> str:
    seed = f"{workspace_id}:{dataset_id}:{refresh_id}:{status}"
    return str(uuid.uuid5(_REFRESH_EVENT_NAMESPACE, seed))


def normalize_refresh_event(
    refresh: dict,
    workspace_id: str,
    dataset_id: str,
    workspace_name: str | None = None,
    dataset_name: str | None = None,
    source: str = "collector",
    emitted_at: datetime | None = None,
) -> dict:
    refresh_id = refresh.get("id") or refresh.get("requestId") or refresh.get("refreshId")
    if not refresh_id:
        raise ValueError("Refresh record missing id")

    status = refresh.get("status") or "Unknown"
    start_time = _parse_utc(refresh.get("startTime"))
    end_time = _parse_utc(refresh.get("endTime"))
    if not start_time:
        raise ValueError("Refresh record missing startTime")
    duration_sec = None
    if start_time and end_time:
        duration_sec = int((end_time - start_time).total_seconds())

    error_message = None
    if status in {"Failed", "Cancelled"}:
        error_message = (
            refresh.get("serviceExceptionJson")
            or refresh.get("error")
            or refresh.get("errorMessage")
        )

    emitted = emitted_at or datetime.now(timezone.utc)

    return {
        "schema_version": "1.0",
        "event_id": _build_event_id(workspace_id, dataset_id, refresh_id, status),
        "emitted_at": _to_rfc3339(emitted),
        "workspace_id": workspace_id,
        "workspace_name": workspace_name or workspace_id,
        "dataset_id": dataset_id,
        "dataset_name": dataset_name or dataset_id,
        "refresh_id": refresh_id,
        "status": status,
        "start_time": _to_rfc3339(start_time),
        "end_time": _to_rfc3339(end_time) if end_time else None,
        "duration_sec": duration_sec,
        "error_message": error_message,
        "source": source,
    }


def normalize_refresh_history(
    refreshes: list[dict],
    workspace_id: str,
    dataset_id: str,
    workspace_name: str | None = None,
    dataset_name: str | None = None,
    source: str = "collector",
) -> list[dict]:
    return [
        normalize_refresh_event(
            refresh,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            workspace_name=workspace_name,
            dataset_name=dataset_name,
            source=source,
        )
        for refresh in refreshes
    ]
