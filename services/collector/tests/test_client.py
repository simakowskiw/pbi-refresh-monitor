from datetime import datetime, timedelta, timezone

from collector.client import _parse_retry_after


def test_parse_retry_after_seconds():
    assert _parse_retry_after("5") == 5.0


def test_parse_retry_after_http_date():
    retry_at = datetime.now(timezone.utc) + timedelta(seconds=2)
    value = retry_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
    parsed = _parse_retry_after(value)

    assert parsed is not None
    assert parsed >= 0


def test_parse_retry_after_invalid():
    assert _parse_retry_after("not-a-date") is None
