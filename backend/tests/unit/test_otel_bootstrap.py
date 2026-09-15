"""The OTel seam stays dormant unless the flag is on and an endpoint is wired."""

import sys

import pytest

import otel_bootstrap


@pytest.fixture(autouse=True)
def _clear_otel_env(monkeypatch):
    monkeypatch.delenv(otel_bootstrap.OTEL_ENDPOINT_ENV, raising=False)
    monkeypatch.delenv(otel_bootstrap.OTEL_ENABLED_ENV, raising=False)


def _enable(monkeypatch):
    monkeypatch.setenv(otel_bootstrap.OTEL_ENABLED_ENV, "true")
    monkeypatch.setenv(otel_bootstrap.OTEL_ENDPOINT_ENV, "http://collector:4318")


class TestOtelRequested:
    def test_false_by_default(self):
        assert otel_bootstrap.otel_requested() is False

    def test_false_with_endpoint_but_flag_off(self, monkeypatch):
        monkeypatch.setenv(otel_bootstrap.OTEL_ENDPOINT_ENV, "http://collector:4318")
        assert otel_bootstrap.otel_requested() is False

    def test_false_with_flag_but_no_endpoint(self, monkeypatch):
        monkeypatch.setenv(otel_bootstrap.OTEL_ENABLED_ENV, "true")
        assert otel_bootstrap.otel_requested() is False

    def test_false_when_flag_not_true(self, monkeypatch):
        monkeypatch.setenv(otel_bootstrap.OTEL_ENABLED_ENV, "false")
        monkeypatch.setenv(otel_bootstrap.OTEL_ENDPOINT_ENV, "http://collector:4318")
        assert otel_bootstrap.otel_requested() is False

    def test_true_with_flag_and_endpoint(self, monkeypatch):
        _enable(monkeypatch)
        assert otel_bootstrap.otel_requested() is True


class TestBootstrapOtel:
    def test_noop_when_dormant_does_not_import_util(self, monkeypatch):
        def explode(*_args, **_kwargs):
            raise AssertionError("must not touch the util when dormant")

        monkeypatch.setattr(otel_bootstrap, "flush_otel", explode)
        otel_bootstrap.bootstrap_otel(service_name="consult-worker")

    def test_warns_when_requested_but_extra_missing(self, monkeypatch, settings):
        _enable(monkeypatch)
        # The [otel] extra is installed in CI, so fake its absence to reach the ImportError branch.
        monkeypatch.setitem(sys.modules, "i_dot_ai_utilities.logging._otel", None)
        warnings = []
        monkeypatch.setattr(
            settings.LOGGER, "warning", lambda msg, **kw: warnings.append((msg, kw))
        )
        otel_bootstrap.bootstrap_otel(service_name="consult-worker")
        assert warnings
        assert warnings[0][1]["service_name"] == "consult-worker"


class TestFlushOtel:
    def test_noop_when_dormant(self):
        otel_bootstrap.flush_otel()


class TestExecutionSpan:
    def test_runs_body_when_dormant(self):
        ran = False
        with otel_bootstrap.execution_span("rq.job probe", context_id="abc", rq_job="probe"):
            ran = True
        assert ran

    def test_body_exception_propagates(self):
        with (
            pytest.raises(ValueError, match="boom"),
            otel_bootstrap.execution_span("rq.job probe"),
        ):
            raise ValueError("boom")
