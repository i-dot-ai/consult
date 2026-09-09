import pytest

from sentry_context import (
    NON_PROD_PERF_SAMPLE_RATE,
    PROD_PERF_SAMPLE_RATE,
    default_perf_sample_rate,
    sentry_before_send,
)


def _event(mechanism=None, tags=None):
    exception_value = {}
    if mechanism is not None:
        exception_value["mechanism"] = mechanism
    return {"exception": {"values": [exception_value]}, "tags": tags or {}}


class TestSentryBeforeSend:
    """Only uncaught exceptions reach Sentry; handled exceptions are dropped."""

    def test_drops_handled_exception(self):
        event = _event(mechanism={"type": "generic", "handled": True})

        assert sentry_before_send(event, {}) is None

    def test_drops_handled_exception_with_tags(self):
        """Tags on an event do not affect the handled filter."""
        event = _event(
            mechanism={"type": "generic", "handled": True},
            tags={"other_tag": "value"},
        )

        assert sentry_before_send(event, {}) is None

    def test_keeps_unhandled_exception(self):
        """e.g. mechanism={"type": "django", "handled": False} - an exception that
        escaped uncaught and was only caught by the Django integration."""
        event = _event(mechanism={"type": "django", "handled": False})

        assert sentry_before_send(event, {}) is event

    def test_keeps_event_with_no_mechanism(self):
        """Events with no mechanism field pass through."""
        event = _event()

        assert sentry_before_send(event, {}) is event


class TestDefaultPerfSampleRate:
    def test_prod_samples_a_fraction(self):
        assert default_perf_sample_rate("prod") == PROD_PERF_SAMPLE_RATE

    @pytest.mark.parametrize("environment", ["dev", "preprod", "local"])
    def test_non_prod_keeps_everything(self, environment):
        assert default_perf_sample_rate(environment) == NON_PROD_PERF_SAMPLE_RATE

    @pytest.mark.parametrize("environment", ["PROD", "Prod"])
    def test_prod_match_is_case_insensitive(self, environment):
        assert default_perf_sample_rate(environment) == PROD_PERF_SAMPLE_RATE

    def test_prod_default_is_lower_than_non_prod(self):
        """The whole point of the ticket: prod deliberately samples less."""
        assert PROD_PERF_SAMPLE_RATE < NON_PROD_PERF_SAMPLE_RATE
