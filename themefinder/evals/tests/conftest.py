import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval_types import Case
from settings import (
    EvalRunnerSource,
    EvalRunSettings,
    EvalSettings,
    GatewaySettings,
    LangfuseSettings,
    LogLevel,
)
from utils import gateway


def make_eval_settings(
    *,
    auto_eval_model: str | None = "test-model",
    environment: str = "test",
    git_sha: str = "abcdef0",
    gateway_url: str | None = "https://gateway.example.invalid",
    gateway_api_key: str | None = "test-key",  # pragma: allowlist secret
    langfuse: LangfuseSettings | None = None,
    engine: EvalRunnerSource = "pydantic_evals",
    dataset_source: str | None = "local",
    artefact_store: str | None = "local",
    log_level: LogLevel = "INFO",
) -> EvalSettings:
    """Build explicit eval settings for consumers under test.

    Runtime modules use the process-wide ``eval_settings`` snapshot. Tests
    patch that dependency with this helper rather than reconfiguring process
    environment variables and clearing the settings factory cache.
    """
    return EvalSettings(
        auto_eval_model=auto_eval_model,
        environment=environment,
        git_sha=git_sha,
        gateway=GatewaySettings(url=gateway_url, api_key=gateway_api_key),
        langfuse=langfuse,
        eval=EvalRunSettings(
            engine=engine,
            dataset_source=dataset_source,
            artefact_store=artefact_store,
        ),
        log_level=log_level,
    )


def set_gateway_credentials(
    monkeypatch,
    url: str = "https://gateway.example.invalid",
    api_key: str = "test-key",
) -> None:
    """Fake gateway credentials for code that calls gateway.gateway_credentials().

    Tests interested in callers rather than settings validation patch the
    helper directly to avoid depending on a developer's environment.
    """
    monkeypatch.setattr(gateway, "gateway_credentials", lambda *a, **k: (url, api_key))


def make_gateway_model(
    name: str,
    family: str | None = "gpt",
    health: str = "healthy",
    supports_reasoning: bool = False,
) -> gateway.GatewayModel:
    """Shared GatewayModel test fixture builder for test_gateway.py / test_benchmark.py."""
    return gateway.GatewayModel(
        name=name, family=family, health=health, supports_reasoning=supports_reasoning
    )


def make_case(
    inputs: dict | None = None,
    expected_output: dict | None = None,
    case_id: str = "case-1",
) -> Case:
    """Shared Case test fixture builder for evaluator adapter tests."""
    return Case(id=case_id, inputs=inputs or {}, expected_output=expected_output)


def _themes(*labels: str, description: str = "desc") -> list[dict[str, str]]:
    """Build theme records in the canonical evaluator input shape."""
    return [
        {
            "topic_id": f"theme-{index}",
            "topic_label": label,
            "topic_description": description,
        }
        for index, label in enumerate(labels)
    ]
