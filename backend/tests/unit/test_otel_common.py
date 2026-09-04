import otel_common


def test_not_requested_when_disabled(otel_disabled):
    assert otel_common.otel_requested() is False


def test_requested_when_enabled(otel_enabled):
    assert otel_common.otel_requested() is True
