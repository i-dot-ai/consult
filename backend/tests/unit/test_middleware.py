from unittest.mock import patch

import structlog
from django.http import HttpResponse

from middleware import (
    CONTEXT_ID_HEADER,
    MAX_CONTEXT_ID_LEN,
    RequestCorrelationMiddleware,
)


def _make_middleware(captured=None):
    """Build the middleware wrapping a trivial view that records the bound context."""

    def view(request):
        if captured is not None:
            captured["context_id"] = structlog.contextvars.get_contextvars().get("context_id")
            captured["path"] = structlog.contextvars.get_contextvars().get("path")
        return HttpResponse(status=200)

    return RequestCorrelationMiddleware(view)


def test_generates_context_id_when_header_absent(request_factory):
    captured = {}
    middleware = _make_middleware(captured)

    response = middleware(request_factory.get("/api/consultations/"))

    assert captured["context_id"]  # a generated id was bound during the request
    assert response[CONTEXT_ID_HEADER] == captured["context_id"]


def test_reuses_inbound_context_id(request_factory):
    captured = {}
    middleware = _make_middleware(captured)
    inbound = "inbound-correlation-id"

    response = middleware(request_factory.get("/api/consultations/", headers={"x-context-id": inbound}))

    assert captured["context_id"] == inbound
    assert response[CONTEXT_ID_HEADER] == inbound


def test_oversized_inbound_context_id_is_rejected(request_factory):
    captured = {}
    middleware = _make_middleware(captured)
    oversized = "a" * (MAX_CONTEXT_ID_LEN + 50)

    response = middleware(
        request_factory.get("/api/consultations/", headers={"x-context-id": oversized})
    )

    # Falls back to the generated id rather than binding/echoing the untrusted value.
    assert captured["context_id"] != oversized
    assert len(response[CONTEXT_ID_HEADER]) <= MAX_CONTEXT_ID_LEN


def test_non_printable_inbound_context_id_is_rejected(request_factory):
    captured = {}
    middleware = _make_middleware(captured)
    malicious = "id\n\rINJECTED level=error"

    response = middleware(
        request_factory.get("/api/consultations/", headers={"x-context-id": malicious})
    )

    assert captured["context_id"] != malicious
    assert response[CONTEXT_ID_HEADER].isprintable()


def test_binds_request_metadata(request_factory):
    captured = {}
    middleware = _make_middleware(captured)

    middleware(request_factory.get("/api/consultations/"))

    assert captured["path"] == "/api/consultations/"


def test_context_does_not_leak_between_requests(request_factory):
    captured_first = {}
    first = _make_middleware(captured_first)
    first(request_factory.get("/api/consultations/", headers={"x-context-id": "first-id"}))

    captured_second = {}
    second = _make_middleware(captured_second)
    second(request_factory.get("/api/consultations/"))

    # The second request neither inherits the first id nor its custom fields.
    assert captured_second["context_id"] != "first-id"


def test_pre_bound_stale_context_id_is_replaced(request_factory):
    structlog.contextvars.bind_contextvars(context_id="stale-value")
    try:
        captured = {}
        middleware = _make_middleware(captured)

        middleware(request_factory.get("/api/consultations/"))

        assert captured["context_id"] not in ("stale-value", "unknown")
    finally:
        structlog.contextvars.unbind_contextvars("context_id")


def test_health_path_is_excluded(request_factory):
    middleware = _make_middleware()

    response = middleware(request_factory.get("/api/health/"))

    assert CONTEXT_ID_HEADER not in response


def test_health_path_still_refreshes_context(request_factory):
    """Excluded paths are still refreshed so a pooled thread never reuses an id."""
    structlog.contextvars.bind_contextvars(context_id="stale-value")
    try:
        captured = {}
        middleware = _make_middleware(captured)

        middleware(request_factory.get("/api/health/"))

        assert captured["context_id"] not in ("stale-value", "unknown")
    finally:
        structlog.contextvars.unbind_contextvars("context_id")


def test_context_id_set_as_sentry_tag(request_factory):
    middleware = _make_middleware()

    with patch("middleware.sentry_sdk.set_tag") as mock_set_tag:
        response = middleware(request_factory.get("/api/consultations/"))

    mock_set_tag.assert_called_once_with("context_id", response[CONTEXT_ID_HEADER])
