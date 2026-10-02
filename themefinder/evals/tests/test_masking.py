"""Tests for Langfuse telemetry redaction and its wiring onto the client."""

from __future__ import annotations

from settings import get_settings
from utils.langfuse import get_langfuse_context
from utils.masking import mask_sensitive


class TestMaskSensitive:
    def test_redacts_email(self):
        assert mask_sensitive("contact a.user@example.com now") == (
            "contact [redacted] now"
        )

    def test_redacts_phone_number(self):
        assert mask_sensitive("call 07911 123456 today") == "call [redacted] today"

    def test_redacts_international_phone_number(self):
        assert mask_sensitive("call +44 20 7946 0958 now") == "call [redacted] now"

    def test_keeps_dates_and_long_ids(self):
        assert mask_sensitive("ref 2026-01-29 id 123456789012") == (
            "ref 2026-01-29 id 123456789012"
        )

    def test_keeps_model_and_version_strings(self):
        assert (
            mask_sensitive("gpt-4-1106-preview v1.2.3") == "gpt-4-1106-preview v1.2.3"
        )

    def test_leaves_plain_text_untouched(self):
        assert mask_sensitive("theme about transport") == "theme about transport"

    def test_recurses_into_dict_and_list(self):
        out = mask_sensitive({"a": ["x@y.com", "fine"], "b": "ok"})
        assert out == {"a": ["[redacted]", "fine"], "b": "ok"}

    def test_passes_non_strings_through(self):
        assert mask_sensitive(4.5) == 4.5
        assert mask_sensitive(None) is None


class TestClientMaskWiring:
    def test_get_langfuse_context_passes_mask_to_client(self, monkeypatch):
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")  # pragma: allowlist secret
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_BASE_URL", "https://langfuse.example.invalid")
        monkeypatch.setenv("THEMEFINDER_EVAL_DATASET_SOURCE", "langfuse")
        get_settings.cache_clear()

        captured: dict = {}

        class _FakeLangfuse:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        monkeypatch.setattr("langfuse.Langfuse", _FakeLangfuse)

        get_langfuse_context(
            session_id="s", eval_type="generation", settings=get_settings()
        )

        assert captured["mask"] is mask_sensitive
