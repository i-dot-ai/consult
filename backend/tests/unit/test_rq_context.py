import pytest
import structlog

import rq_context
from logging_context import get_context_id, rebind_context


@pytest.fixture(autouse=True)
def clear_logging_context():
    """These tests read/write process-global structlog contextvars, and the suite
    runs with --random-order, so each test must start and end from a clean slate."""
    structlog.contextvars.clear_contextvars()
    yield
    structlog.contextvars.clear_contextvars()


@rq_context.job("default", timeout=60)
def probe_job(value):
    """Module-level because RQ stores enqueued functions by dotted path and
    re-imports them at execution time -- a job defined inside a test can't be
    resolved that way."""
    return get_context_id(), value


@rq_context.job("default", timeout=60)
def probe_job_kwargs(**kwargs):
    return kwargs


class TestGetContextId:
    def test_returns_none_when_nothing_is_bound(self):
        assert get_context_id() is None

    def test_returns_the_currently_bound_context_id(self):
        structlog.contextvars.bind_contextvars(context_id="bound-id")

        assert get_context_id() == "bound-id"


class TestRebindContext:
    def test_binds_the_given_context_id(self):
        rebind_context("known-id")

        assert get_context_id() == "known-id"

    def test_none_mints_a_fresh_context_id(self):
        rebind_context(None)

        assert get_context_id() is not None

    def test_clears_fields_set_since_the_previous_call(self):
        structlog.contextvars.bind_contextvars(consultation_code="stale-value")

        rebind_context("known-id")

        assert "consultation_code" not in structlog.contextvars.get_contextvars()


class TestRQContextJob:
    """rq_context.job is the drop-in replacement for django_rq.job: it auto-fills
    context_id at enqueue time and strips and rebinds it at execution time.

    RQ_QUEUES has ASYNC=False in test settings, so .delay()/.enqueue() run the job
    synchronously through the real, unmocked enqueue path (backed by the real Redis
    service CI/local dev both run)."""

    def test_ambient_context_id_survives_a_real_delay_round_trip(self):
        """The one test asserting context_id survives the full enqueue -> execution
        round trip.

        The job.kwargs assertion is load-bearing: ASYNC=False runs the job in the
        same process as the caller, so the body could read the caller's still-bound
        contextvars even if propagation were completely broken. Checking the stored
        job payload proves the id was genuinely captured into the enqueued kwargs,
        not just leaked through shared process state."""
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
        """Workers are long-lived processes executing many unrelated jobs
        sequentially -- one job's context_id must never bleed into the next job
        when that job arrives without its own."""
        probe_job(1, context_id="first-call-id")

        seen_context_id, _ = probe_job(2)

        assert seen_context_id != "first-call-id"

    def test_delay_and_enqueue_are_the_same_wrapped_function(self):
        """Production enqueues via both styles (.delay() and .enqueue()); this is
        the only guard that .enqueue is wrapped too, since the other tests all use
        .delay or call the job directly."""
        assert probe_job.delay is probe_job.enqueue
