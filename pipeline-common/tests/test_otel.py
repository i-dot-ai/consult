"""The Batch OTel seam stays dormant unless the flag is on and an endpoint is wired."""

import sys
from unittest.mock import MagicMock

import pytest

from pipeline_common import otel


@pytest.fixture(autouse=True)
def _clear_otel_env(monkeypatch):
    monkeypatch.delenv(otel.OTEL_ENDPOINT_ENV, raising=False)
    monkeypatch.delenv(otel.OTEL_ENABLED_ENV, raising=False)


def _enable(monkeypatch):
    monkeypatch.setenv(otel.OTEL_ENABLED_ENV, "true")
    monkeypatch.setenv(otel.OTEL_ENDPOINT_ENV, "http://collector:4318")


class TestOtelRequested:
    def test_false_by_default(self):
        assert otel.otel_requested() is False

    def test_false_with_endpoint_but_flag_off(self, monkeypatch):
        monkeypatch.setenv(otel.OTEL_ENDPOINT_ENV, "http://collector:4318")
        assert otel.otel_requested() is False

    def test_false_with_flag_but_no_endpoint(self, monkeypatch):
        monkeypatch.setenv(otel.OTEL_ENABLED_ENV, "true")
        assert otel.otel_requested() is False

    def test_false_when_flag_not_true(self, monkeypatch):
        monkeypatch.setenv(otel.OTEL_ENABLED_ENV, "false")
        monkeypatch.setenv(otel.OTEL_ENDPOINT_ENV, "http://collector:4318")
        assert otel.otel_requested() is False

    def test_true_with_flag_and_endpoint(self, monkeypatch):
        _enable(monkeypatch)
        assert otel.otel_requested() is True


class TestBootstrapOtel:
    def test_noop_when_dormant(self):
        logger = MagicMock()
        otel.bootstrap_otel("consult-pipeline-sign-off", logger)
        logger.warning.assert_not_called()

    def test_warns_when_requested_but_extra_missing(self, monkeypatch):
        _enable(monkeypatch)
        # The [otel] extra is installed in CI, so fake its absence to reach the ImportError branch.
        monkeypatch.setitem(sys.modules, "i_dot_ai_utilities.logging._otel", None)
        logger = MagicMock()
        otel.bootstrap_otel("consult-pipeline-sign-off", logger)
        logger.warning.assert_called_once()
        assert logger.warning.call_args.kwargs["service_name"] == "consult-pipeline-sign-off"


class TestExecutionSpan:
    def test_runs_body_when_dormant(self):
        ran = False
        with otel.execution_span("batch.find_themes", context_id="abc", consultation_code="X"):
            ran = True
        assert ran

    def test_body_exception_propagates(self):
        with (
            pytest.raises(ValueError, match="boom"),
            otel.execution_span("batch.find_themes"),
        ):
            raise ValueError("boom")


class TestFlushOtel:
    def test_noop_when_dormant(self):
        otel.flush_otel()
