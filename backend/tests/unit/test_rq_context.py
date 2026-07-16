import pathlib
from unittest.mock import Mock, patch

import pytest
import structlog
from rq.utils import import_attribute

import rq_context
from logging_context import get_context_id, rebind_context

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[2]
THIS_FILE = pathlib.Path(__file__).resolve()


@pytest.fixture(autouse=True)
def clear_logging_context():
    """These tests read/write process-global structlog contextvars, and the suite
    runs with --random-order, so each test must start and end from a clean slate."""
    structlog.contextvars.clear_contextvars()
    yield
    structlog.contextvars.clear_contextvars()


@rq_context.job("default", timeout=60)
def probe_job(value):
    """Module-level so it has a stable dotted path, matching how RQ resolves jobs
    enqueued by string name (as the import Lambdas do)."""
    return get_context_id(), value


@rq_context.job("default", timeout=60)
def probe_job_kwargs(**kwargs):
    return kwargs


def _make_stub_rq_job():
    """Stand-in for django_rq.job: skips real Redis/RQ entirely and just attaches a
    mock .delay/.enqueue, so enqueue-time tests can assert what rq_context.job
    forwarded to it without touching a live queue."""
    delay_mock = Mock(name="rq_delay", return_value="fake-job")

    def stub(*_job_args, **_job_kwargs):
        def decorator(f):
            f.delay = delay_mock
            f.enqueue = delay_mock
            return f

        return decorator

    return stub, delay_mock


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


class TestJob:
    """rq_context.job is the drop-in replacement for django_rq.job: it strips and
    rebinds context_id at execution time, auto-fills it at enqueue time, and must
    remain dispatchable exactly like a normal RQ job (by object or by dotted name,
    as the import Lambdas do)."""

    def test_explicit_context_id_is_bound_before_the_job_runs(self):
        seen_context_id, value = probe_job(42, context_id="explicit-id")

        assert seen_context_id == "explicit-id"
        assert value == 42

    def test_context_id_is_stripped_and_never_reaches_the_job_body(self):
        result = probe_job_kwargs(foo="bar", context_id="explicit-id")

        assert result == {"foo": "bar"}

    def test_no_context_id_mints_a_fresh_one(self):
        seen_context_id, _ = probe_job(1)

        assert seen_context_id is not None

    def test_stale_context_from_a_previous_call_does_not_leak(self):
        probe_job(1, context_id="first-call-id")

        seen_context_id, _ = probe_job(2)

        assert seen_context_id != "first-call-id"

    @patch("rq_context._rq_job")
    def test_ambient_context_id_is_used_when_caller_does_not_pass_one(self, mock_rq_job):
        stub, delay_mock = _make_stub_rq_job()
        mock_rq_job.side_effect = stub
        rebind_context("ambient-id")

        @rq_context.job("default")
        def sample(x):
            return x

        sample.delay(1)

        delay_mock.assert_called_once_with(1, context_id="ambient-id")

    @patch("rq_context._rq_job")
    def test_explicit_context_id_overrides_ambient(self, mock_rq_job):
        stub, delay_mock = _make_stub_rq_job()
        mock_rq_job.side_effect = stub
        rebind_context("ambient-id")

        @rq_context.job("default")
        def sample(x):
            return x

        sample.delay(1, context_id="explicit-id")

        delay_mock.assert_called_once_with(1, context_id="explicit-id")

    @patch("rq_context._rq_job")
    def test_no_ambient_context_forwards_none(self, mock_rq_job):
        stub, delay_mock = _make_stub_rq_job()
        mock_rq_job.side_effect = stub
        # clear_logging_context fixture guarantees nothing is bound here

        @rq_context.job("default")
        def sample(x):
            return x

        sample.delay(1)

        delay_mock.assert_called_once_with(1, context_id=None)

    def test_delay_and_enqueue_are_the_same_wrapped_function(self):
        @rq_context.job("default", timeout=60)
        def sample(x):
            return x

        assert sample.delay is sample.enqueue

    def test_dotted_path_dispatch_still_rebinds_context_id(self):
        """Confirms the mechanism any external caller enqueueing by dotted string
        name (queue.enqueue("data_pipeline.jobs.foo", ...), rather than importing
        the Python object) would depend on: RQ's own import_attribute resolves to
        our wrapper, and calling it the way the worker does still rebinds
        context_id correctly."""
        resolved = import_attribute("tests.unit.test_rq_context.probe_job")

        seen_context_id, value = resolved(7, context_id="from-external-caller")

        assert seen_context_id == "from-external-caller"
        assert value == 7

    def test_ambient_context_id_survives_a_real_delay_round_trip(self):
        """The other TestJob tests prove enqueue-time auto-fill and execution-time
        rebind as two separate, isolated halves (one against a stubbed _rq_job,
        one by calling the job body directly) -- neither actually proves the two
        halves connect correctly. This one does: RQ_QUEUES ASYNC=False in test
        settings means .delay() runs the job synchronously through the real,
        unmocked enqueue path (backed by the real Redis service CI/local dev both
        run), so this is the one test asserting context_id survives the full
        enqueue -> execution round trip, not just its two halves in isolation."""
        rebind_context("ambient-real-id")

        job = probe_job.delay(42)

        assert job.result == ("ambient-real-id", 42)


class TestNoBareDjangoRqUsage:
    """Guards against a future job silently opting out of context_id propagation by
    importing django_rq.job directly instead of rq_context.job."""

    def test_no_module_imports_django_rq_job_directly(self):
        offenders = []
        for path in BACKEND_ROOT.rglob("*.py"):
            if ".venv" in path.parts or path in (THIS_FILE, BACKEND_ROOT / "rq_context.py"):
                continue
            text = path.read_text()
            if "from django_rq import job" in text:
                offenders.append(str(path.relative_to(BACKEND_ROOT)))

        assert offenders == [], (
            f"Use `from rq_context import job` instead of django_rq.job directly in: {offenders}"
        )
