"""Tests for the Langfuse context and metadata built in utils.langfuse."""

from dataclasses import replace

from conftest import make_eval_settings
from settings import LangfuseSettings
from utils.langfuse import get_langfuse_context


def test_context_metadata_carries_judge_and_only_str_values(monkeypatch):
    """v4 propagates str metadata only, and None means the key doesn't apply."""
    monkeypatch.setattr("langfuse.Langfuse", lambda **kwargs: object())
    settings = make_eval_settings(
        dataset_source="langfuse",
        langfuse=LangfuseSettings(
            secret_key="sk-test",  # pragma: allowlist secret
            public_key="pk-test",
            base_url="https://langfuse.example.invalid",
            project_id=None,
        ),
    )

    context = get_langfuse_context(
        session_id="s",
        eval_type="generation",
        metadata={"run_number": 2, "reasoning_effort": None},
        settings=replace(settings, judge_model="judge-m"),
    )

    assert context.metadata["judge_model"] == "judge-m"
    assert context.metadata["aggregate"] == "false"
    assert context.metadata["run_number"] == "2"
    assert "reasoning_effort" not in context.metadata
    assert all(isinstance(value, str) for value in context.metadata.values())
