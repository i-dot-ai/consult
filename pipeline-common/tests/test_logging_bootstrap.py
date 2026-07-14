from unittest.mock import patch

from i_dot_ai_utilities.logging.types.enrichment_types import ExecutionEnvironmentType

from pipeline_common import bootstrap_logger


def test_execution_environment_defaults_to_local(monkeypatch):
    monkeypatch.delenv("EXECUTION_CONTEXT", raising=False)
    with patch("pipeline_common.logging_bootstrap.StructuredLogger") as mock_logger_cls:
        bootstrap_logger()
    options = mock_logger_cls.call_args.kwargs["options"]
    assert options["execution_environment"] == ExecutionEnvironmentType.LOCAL


def test_execution_environment_is_fargate_when_running_in_batch(monkeypatch):
    monkeypatch.setenv("EXECUTION_CONTEXT", "batch")
    with patch("pipeline_common.logging_bootstrap.StructuredLogger") as mock_logger_cls:
        bootstrap_logger()
    options = mock_logger_cls.call_args.kwargs["options"]
    assert options["execution_environment"] == ExecutionEnvironmentType.FARGATE


def test_context_id_is_adopted_when_present(monkeypatch):
    monkeypatch.setenv("CONTEXT_ID", "incoming-context-id")
    with patch("pipeline_common.logging_bootstrap.StructuredLogger"):
        logger = bootstrap_logger()
    logger.set_context_field.assert_any_call("context_id", "incoming-context-id")


def test_context_id_is_left_untouched_when_absent(monkeypatch):
    monkeypatch.delenv("CONTEXT_ID", raising=False)
    with patch("pipeline_common.logging_bootstrap.StructuredLogger"):
        logger = bootstrap_logger()
    context_id_calls = [
        call for call in logger.set_context_field.call_args_list if call.args[0] == "context_id"
    ]
    assert context_id_calls == []


def test_sentry_is_not_initialized_when_dsn_absent(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    with (
        patch("pipeline_common.logging_bootstrap.StructuredLogger"),
        patch("pipeline_common.logging_bootstrap.sentry_sdk") as mock_sentry_sdk,
    ):
        bootstrap_logger()
    mock_sentry_sdk.init.assert_not_called()


def test_sentry_is_initialized_when_dsn_present(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://example.invalid/dsn")
    monkeypatch.setenv("ENVIRONMENT", "test")
    with (
        patch("pipeline_common.logging_bootstrap.StructuredLogger"),
        patch("pipeline_common.logging_bootstrap.sentry_sdk") as mock_sentry_sdk,
    ):
        bootstrap_logger()
    mock_sentry_sdk.init.assert_called_once_with(
        dsn="https://example.invalid/dsn",
        environment="test",
        traces_sample_rate=1.0,
    )
