"""Unit tests for evaluation backend resolution."""

from types import SimpleNamespace
from uuid import UUID

import pytest
from adapters.artefact_stores import LangfuseArtefactStore, LocalJSONArtefactStore
from adapters.datasets import LangfuseDatasetAdapter, LocalJSONDatasetAdapter
from adapters.runners import PydanticEvalsRunner
from config import EvalBackends, resolve_backends
from datasets import DatasetConfig
from settings import (
    EvalRunSettings,
    EvalSettings,
    GatewaySettings,
    LangfuseSettings,
)
from utils import langfuse as langfuse_utils
from utils.langfuse import LangfuseContext

DATASET_CONFIG = DatasetConfig(dataset="gambling_XS", component="generation")
TEST_LANGFUSE_SECRET_KEY = "sk-test"  # pragma: allowlist secret


def _settings(
    dataset_source: str | None,
    artefact_store: str | None,
    *,
    langfuse: LangfuseSettings | None = None,
) -> EvalSettings:
    if langfuse is None and "langfuse" in (dataset_source, artefact_store):
        langfuse = LangfuseSettings(
            secret_key=TEST_LANGFUSE_SECRET_KEY,
            public_key="public",
            base_url="https://langfuse.example.invalid",
            project_id=None,
        )

    return EvalSettings(
        auto_eval_model="test-model",
        environment="test",
        git_sha="abcdef0",
        gateway=GatewaySettings(url=None, api_key=None),
        langfuse=langfuse,
        eval=EvalRunSettings(
            engine="pydantic_evals",
            dataset_source=dataset_source,
            artefact_store=artefact_store,
        ),
    )


@pytest.mark.parametrize(
    (
        "dataset_source",
        "artefact_store",
        "dataset_type",
        "artefact_type",
    ),
    [
        ("local", "local", LocalJSONDatasetAdapter, LocalJSONArtefactStore),
        ("langfuse", "local", LangfuseDatasetAdapter, LocalJSONArtefactStore),
        ("local", "langfuse", LocalJSONDatasetAdapter, LangfuseArtefactStore),
        ("langfuse", "langfuse", LangfuseDatasetAdapter, LangfuseArtefactStore),
    ],
)
def test_resolves_dataset_and_artefact_sources_independently(
    dataset_source,
    artefact_store,
    dataset_type,
    artefact_type,
):
    client = SimpleNamespace()
    context = LangfuseContext(client=client)

    backends = resolve_backends(
        DATASET_CONFIG,
        settings=_settings(dataset_source, artefact_store),
        context=context if "langfuse" in (dataset_source, artefact_store) else None,
    )

    assert isinstance(backends, EvalBackends)
    assert isinstance(backends.dataset, dataset_type)
    assert isinstance(backends.runner, PydanticEvalsRunner)
    assert isinstance(backends.artefacts, artefact_type)

    if isinstance(backends.dataset, LangfuseDatasetAdapter):
        assert backends.dataset.client is client
    if isinstance(backends.artefacts, LangfuseArtefactStore):
        assert backends.artefacts.context is context
        assert backends.artefacts.owns_context is False


def test_unset_sources_default_to_local(monkeypatch):
    def fail_if_called(**kwargs):
        pytest.fail(f"Langfuse context should not be created: {kwargs}")

    monkeypatch.setattr(langfuse_utils, "get_langfuse_context", fail_if_called)

    backends = resolve_backends(DATASET_CONFIG, settings=_settings(None, None))

    assert isinstance(backends.dataset, LocalJSONDatasetAdapter)
    assert isinstance(backends.artefacts, LocalJSONArtefactStore)


def test_creates_one_shared_langfuse_context(monkeypatch):
    client = SimpleNamespace()
    context = LangfuseContext(client=client, session_id="shared-session")
    calls = []

    def fake_get_langfuse_context(**kwargs):
        calls.append(kwargs)
        return context

    monkeypatch.setattr(
        langfuse_utils, "get_langfuse_context", fake_get_langfuse_context
    )
    settings = _settings("langfuse", "langfuse")

    backends = resolve_backends(DATASET_CONFIG, settings=settings)

    assert len(calls) == 1
    assert calls[0]["eval_type"] == "generation"
    assert calls[0]["metadata"] == {"dataset": "gambling_XS"}
    assert calls[0]["tags"] == ["gambling_XS"]
    assert calls[0]["settings"] is settings
    session_prefix, session_uuid = calls[0]["session_id"].rsplit("_", maxsplit=1)
    assert session_prefix.startswith("eval_gambling_XS_generation_")
    assert UUID(session_uuid).version == 4
    assert backends.dataset.client is client
    assert backends.artefacts.context is context
    assert backends.artefacts.owns_context is True


def test_reuses_caller_context_without_taking_ownership(monkeypatch):
    context = LangfuseContext(client=SimpleNamespace(), session_id="caller-session")

    def fail_if_called(**kwargs):
        pytest.fail(f"Caller context should have been reused: {kwargs}")

    monkeypatch.setattr(langfuse_utils, "get_langfuse_context", fail_if_called)
    incomplete = LangfuseSettings(
        secret_key=None,
        public_key=None,
        base_url=None,
        project_id=None,
    )

    backends = resolve_backends(
        DATASET_CONFIG,
        settings=_settings("local", "langfuse", langfuse=incomplete),
        context=context,
    )

    assert backends.artefacts.context is context
    assert backends.artefacts.owns_context is False


def test_rejects_langfuse_without_credentials_or_context():
    incomplete = LangfuseSettings(
        secret_key=TEST_LANGFUSE_SECRET_KEY,
        public_key=None,
        base_url=None,
        project_id=None,
    )

    with pytest.raises(ValueError, match="Langfuse requires"):
        resolve_backends(
            DATASET_CONFIG,
            settings=_settings("langfuse", "local", langfuse=incomplete),
        )


def test_rejects_disabled_created_context(monkeypatch):
    monkeypatch.setattr(
        langfuse_utils,
        "get_langfuse_context",
        lambda **kwargs: LangfuseContext(client=None),
    )

    with pytest.raises(ValueError, match="context is unavailable"):
        resolve_backends(
            DATASET_CONFIG,
            settings=_settings("langfuse", "langfuse"),
        )
