import pytest
import structlog

import rq_context
from logging_context import get_or_create_context_id, rebind_context


@pytest.fixture(autouse=True)
def clear_logging_context():
    """Tests share process-global structlog contextvars and run with --random-order, so each needs a clean slate."""
    structlog.contextvars.clear_contextvars()
    yield
    structlog.contextvars.clear_contextvars()


@rq_context.job("default", timeout=60)
def probe_job(value):
    """Module-level so RQ can resolve it by dotted path at execution time."""
    return get_or_create_context_id(), value


@rq_context.job("default", timeout=60)
def probe_job_kwargs(**kwargs):
    return kwargs


class TestGetOrCreateContextId:
    def test_mints_and_binds_a_fresh_id_when_nothing_is_bound(self):
        context_id = get_or_create_context_id()

        assert context_id
        assert get_or_create_context_id() == context_id  # stayed bound, not re-minted

    def test_returns_the_currently_bound_context_id(self):
        structlog.contextvars.bind_contextvars(context_id="bound-id")

        assert get_or_create_context_id() == "bound-id"


class TestRebindContext:
    def test_binds_the_given_context_id(self):
        rebind_context("known-id")

        assert get_or_create_context_id() == "known-id"

    def test_none_mints_a_fresh_context_id(self):
        rebind_context(None)

        assert get_or_create_context_id() is not None

    def test_clears_fields_set_since_the_previous_call(self):
        structlog.contextvars.bind_contextvars(consultation_code="stale-value")

        rebind_context("known-id")

        assert "consultation_code" not in structlog.contextvars.get_contextvars()


class TestRQContextJob:
    """rq_context.job auto-fills context_id at enqueue time and rebinds it at execution time;
       ASYNC=False in tests runs .delay()/.enqueue() through the real path."""

    def test_ambient_context_id_survives_a_real_delay_round_trip(self):
        """Proves context_id survives the full enqueue -> execution round trip;
           the job.kwargs check rules out a same-process leak masquerading as propagation."""
        rebind_context("ambient-real-id")

        job = probe_job.delay(42)

        assert job.kwargs == {"context_id": "ambient-real-id"}
        assert job.return_value() == ("ambient-real-id", 42)

    def test_explicit_context_id_overrides_ambient_on_enqueue(self):
        rebind_context("ambient-id")

        job = probe_job.delay(7, context_id="explicit-id")

        assert job.kwargs == {"context_id": "explicit-id"}

    def test_context_id_is_stripped_and_never_reaches_the_job_body(self):
        result = probe_job_kwargs(foo="bar", context_id="explicit-id")

        assert result == {"foo": "bar"}

    def test_stale_context_from_a_previous_call_does_not_leak(self):
        """One job's context_id must never bleed into the next job on a long-lived worker."""
        probe_job(1, context_id="first-call-id")

        seen_context_id, _ = probe_job(2)

        assert seen_context_id != "first-call-id"

    def test_delay_and_enqueue_are_the_same_wrapped_function(self):
        """Production calls both .delay() and .enqueue(); this is the only test guarding .enqueue."""
        assert probe_job.delay is probe_job.enqueue
