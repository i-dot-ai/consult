from datetime import datetime, timezone

from tests.utils import isoformat


def test_isoformat_utc(settings):
    settings.TIME_ZONE = "UTC"

    dt = datetime(2025, 10, 27, 13, 22, 4, 609627, tzinfo=timezone.utc)
    assert isoformat(dt) == "2025-10-27T13:22:04.609627Z"


def test_isoformat_during_bst(settings):
    settings.TIME_ZONE = "Europe/London"

    dt = datetime(2025, 8, 27, 13, 22, 4, 609627, tzinfo=timezone.utc)
    assert isoformat(dt) == "2025-08-27T14:22:04.609627+01:00"


def test_isoformat_during_gmt(settings):
    settings.TIME_ZONE = "Europe/London"

    dt = datetime(2025, 10, 27, 13, 22, 4, 609627, tzinfo=timezone.utc)
    assert isoformat(dt) == "2025-10-27T13:22:04.609627Z"
