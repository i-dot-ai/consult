"""Unit tests for per-platform context providers."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from adapters import context_providers
from adapters.context_providers import build_langfuse_context
from datasets import DatasetConfig
from eval_types import RunLabels
from settings import (
    EvalRunSettings,
    EvalSettings,
    GatewaySettings,
    LangfuseSettings,
)
from utils.langfuse import LangfuseContext

DATASET_CONFIG = DatasetConfig(dataset="gambling_XS", component="generation")


def _settings() -> EvalSettings:
    return EvalSettings(
        auto_eval_model="test-model",
        environment="test",
        git_sha="abcdef0",
        log_level="INFO",
        gateway=GatewaySettings(url=None, api_key=None),
        langfuse=LangfuseSettings(
            secret_key="sk-test",  # pragma: allowlist secret
            public_key="public",
            base_url="https://langfuse.example.invalid",
            project_id=None,
        ),
        eval=EvalRunSettings(
            engine="pydantic_evals",
            dataset_source="langfuse",
            artefact_store="local",
        ),
    )


def test_disabled_supplied_context_is_rejected():
    with pytest.raises(ValueError, match="context is unavailable"):
        build_langfuse_context(
            DATASET_CONFIG, _settings(), LangfuseContext(client=None)
        )


def test_created_context_is_flushed_on_close(monkeypatch):
    context = LangfuseContext(client=SimpleNamespace())
    flush = Mock()
    monkeypatch.setattr(
        context_providers.langfuse_utils, "get_langfuse_context", lambda **_: context
    )
    monkeypatch.setattr(context_providers.langfuse_utils, "flush", flush)

    provided = build_langfuse_context(DATASET_CONFIG, _settings(), None)
    flush.assert_not_called()
    provided.close()

    assert provided.context is context
    flush.assert_called_once_with(context)


def test_labels_name_and_tag_the_created_context(monkeypatch):
    calls = []

    def fake_get_langfuse_context(**kwargs):
        calls.append(kwargs)
        return LangfuseContext(client=SimpleNamespace())

    monkeypatch.setattr(
        context_providers.langfuse_utils,
        "get_langfuse_context",
        fake_get_langfuse_context,
    )
    labels = RunLabels(
        name="comparison_1_gpt_generation_run2",
        tags=("model:gpt", "run:2"),
        metadata={"run_number": 2},
    )

    build_langfuse_context(DATASET_CONFIG, _settings(), None, labels)

    assert calls == [
        {
            "session_id": "comparison_1_gpt_generation_run2",
            "eval_type": "generation",
            "metadata": {"dataset": "gambling_XS", "run_number": 2},
            "tags": ["gambling_XS", "model:gpt", "run:2"],
            "settings": calls[0]["settings"],
        }
    ]


def test_supplied_context_is_not_flushed_on_close(monkeypatch):
    context = LangfuseContext(client=SimpleNamespace())
    flush = Mock()
    monkeypatch.setattr(context_providers.langfuse_utils, "flush", flush)

    provided = build_langfuse_context(DATASET_CONFIG, _settings(), context)
    provided.close()

    assert provided.context is context
    flush.assert_not_called()
