import structlog

from middleware import RequestLoggingContextMiddleware


def _make_capturing_middleware():
    captured_context_ids = []

    def get_response(request):
        captured_context_ids.append(structlog.contextvars.get_contextvars().get("context_id"))
        return "response"

    return RequestLoggingContextMiddleware(get_response), captured_context_ids


def test_refresh_context_called_before_response():
    middleware, captured_context_ids = _make_capturing_middleware()

    middleware(request=object())

    assert len(captured_context_ids) == 1
    context_id = captured_context_ids[0]
    assert context_id is not None
    assert context_id != "unknown"


def test_pre_bound_context_id_is_replaced():
    structlog.contextvars.bind_contextvars(context_id="stale-value")
    try:
        middleware, captured_context_ids = _make_capturing_middleware()

        middleware(request=object())

        assert captured_context_ids[0] != "stale-value"
        assert captured_context_ids[0] != "unknown"
    finally:
        structlog.contextvars.unbind_contextvars("context_id")


def test_sequential_requests_get_different_context_ids():
    middleware, captured_context_ids = _make_capturing_middleware()

    middleware(request=object())
    middleware(request=object())

    assert len(captured_context_ids) == 2
    assert captured_context_ids[0] != captured_context_ids[1]
