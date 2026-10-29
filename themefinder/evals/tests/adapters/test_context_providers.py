"""Unit tests for per-platform context providers."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from adapters import context_providers
from adapters.context_providers import build_langfuse_context
from datasets import DatasetConfig
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


def test_supplied_context_is_not_flushed_on_close(monkeypatch):
    context = LangfuseContext(client=SimpleNamespace())
    flush = Mock()
    monkeypatch.setattr(context_providers.langfuse_utils, "flush", flush)

    provided = build_langfuse_context(DATASET_CONFIG, _settings(), context)
    provided.close()

    assert provided.context is context
    flush.assert_not_called()
