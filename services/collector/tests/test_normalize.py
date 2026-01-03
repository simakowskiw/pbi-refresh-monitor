from collector.normalize import normalize_refresh_event
import pytest


def test_normalize_refresh_event_deterministic_id():
    refresh = {
        "id": "refresh-123",
        "status": "Completed",
        "startTime": "2025-01-03T15:52:10Z",
        "endTime": "2025-01-03T15:57:40Z",
    }

    event_a = normalize_refresh_event(
        refresh,
        workspace_id="workspace-1",
        dataset_id="dataset-1",
        workspace_name="Workspace",
        dataset_name="Dataset",
    )
    event_b = normalize_refresh_event(
        refresh,
        workspace_id="workspace-1",
        dataset_id="dataset-1",
        workspace_name="Workspace",
        dataset_name="Dataset",
    )

    assert event_a["event_id"] == event_b["event_id"]
    assert event_a["duration_sec"] == 330
    assert event_a["start_time"] == "2025-01-03T15:52:10Z"
    assert event_a["end_time"] == "2025-01-03T15:57:40Z"


def test_normalize_requires_start_time():
    refresh = {
        "id": "refresh-123",
        "status": "Completed",
    }

    with pytest.raises(ValueError):
        normalize_refresh_event(
            refresh,
            workspace_id="workspace-1",
            dataset_id="dataset-1",
        )


def test_normalize_failed_refresh_error_message():
    refresh = {
        "id": "refresh-123",
        "status": "Failed",
        "startTime": "2025-01-03T15:52:10Z",
        "endTime": "2025-01-03T15:57:40Z",
        "serviceExceptionJson": "boom",
    }

    event = normalize_refresh_event(
        refresh,
        workspace_id="workspace-1",
        dataset_id="dataset-1",
    )

    assert event["error_message"] == "boom"
