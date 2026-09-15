from unittest.mock import patch

import pytest

from sentry_context import (
    MANUAL_CAPTURE_TAG,
    NON_PROD_PERF_SAMPLE_RATE,
    PROD_PERF_SAMPLE_RATE,
    capture_handled_sentry_exception,
    default_perf_sample_rate,
    sentry_before_send,
)


class TestCaptureHandledSentryException:
    def test_tags_the_capture_as_manual(self):
        error = ValueError("boom")

        with patch("sentry_context.sentry_sdk.capture_exception") as mock_capture:
            capture_handled_sentry_exception(error)

        mock_capture.assert_called_once_with(error, tags={MANUAL_CAPTURE_TAG: "true"})

    def test_preserves_caller_supplied_tags(self):
        error = ValueError("boom")

        with patch("sentry_context.sentry_sdk.capture_exception") as mock_capture:
            capture_handled_sentry_exception(error, tags={"consultation_code": "ABC123"})

        mock_capture.assert_called_once_with(
            error,
            tags={"consultation_code": "ABC123", MANUAL_CAPTURE_TAG: "true"},
        )

    def test_returns_the_underlying_capture_result(self):
        with patch("sentry_context.sentry_sdk.capture_exception", return_value="event-id"):
            result = capture_handled_sentry_exception(ValueError("boom"))

        assert result == "event-id"


def _event(mechanism=None, tags=None):
    exception_value = {}
    if mechanism is not None:
        exception_value["mechanism"] = mechanism
    return {"exception": {"values": [exception_value]}, "tags": tags or {}}


class TestSentryBeforeSend:
    """capture_handled_sentry_exception tags manual captures so they always survive
    filtering; only exceptions Sentry's own integrations marked handled=True (i.e.
    already caught elsewhere) get dropped here."""

    def test_manually_tagged_capture_is_always_sent(self):
        event = _event(
            mechanism={"type": "generic", "handled": True},
            tags={MANUAL_CAPTURE_TAG: "true"},
        )

        assert sentry_before_send(event, {}) is event

    def test_drops_untagged_handled_exception(self):
        """The core case: a plain sentry_sdk.capture_exception() call, with no
        manual-capture tag, defaults to handled=True and must be dropped."""
        event = _event(mechanism={"type": "generic", "handled": True})

        assert sentry_before_send(event, {}) is None

    def test_still_drops_handled_exception_alongside_unrelated_tags(self):
        """Only MANUAL_CAPTURE_TAG bypasses the filter - other tags on the event
        don't count."""
        event = _event(
            mechanism={"type": "generic", "handled": True},
            tags={"other_tag": "value"},
        )

        assert sentry_before_send(event, {}) is None

    def test_keeps_untagged_unhandled_exception(self):
        """e.g. mechanism={"type": "django", "handled": False} - an exception that
        escaped uncaught and was only caught by the Django integration."""
        event = _event(mechanism={"type": "django", "handled": False})

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
