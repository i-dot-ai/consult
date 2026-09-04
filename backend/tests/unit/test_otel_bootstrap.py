from unittest.mock import MagicMock, patch

import pytest

import otel_bootstrap


class TestBootstrapOtel:
    def test_warns_and_continues_when_setup_fails(self):
        logger = MagicMock()
        with patch.object(otel_bootstrap, "configure_otel", side_effect=RuntimeError("boom")):
            otel_bootstrap.bootstrap_otel(logger=logger, service_name="consult-worker-test")
        logger.warning.assert_called_once()
        assert logger.warning.call_args.kwargs["service_name"] == "consult-worker-test"


class TestExecutionSpan:
    def test_runs_body_when_dormant(self, otel_disabled):
        ran = False
        with otel_bootstrap.execution_span("rq.job probe", context_id="abc", rq_job="probe"):
            ran = True
        assert ran

    def test_body_exception_propagates_when_dormant(self, otel_disabled):
        with (
            pytest.raises(ValueError, match="boom"),
            otel_bootstrap.execution_span("rq.job probe"),
        ):
            raise ValueError("boom")


class TestFlushOtel:
    def test_noop_when_dormant(self, otel_disabled):
        otel_bootstrap.flush_otel()
