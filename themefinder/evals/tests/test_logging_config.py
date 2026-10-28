"""Tests for the shared evals logging setup."""

from __future__ import annotations

import logging

import pytest
from conftest import make_eval_settings
from settings import LangfuseSettings
from utils import logging_config
from utils.logging_config import (
    _HumanFormatter,
    _LangfuseLogHandler,
    configure_logging,
    get_logger,
)


@pytest.fixture(autouse=True)
def _reset_logging(monkeypatch):
    monkeypatch.setattr(logging_config, "eval_settings", make_eval_settings())
    logging_config._configured = False
    logging.getLogger("themefinder.evals").handlers.clear()
    yield
    logging_config._configured = False
    logging.getLogger("themefinder.evals").handlers.clear()


def _enable_langfuse(monkeypatch, *, log_level: str = "INFO"):
    monkeypatch.setattr(
        logging_config,
        "eval_settings",
        make_eval_settings(
            dataset_source="langfuse",
            langfuse=LangfuseSettings(
                secret_key="sk-test",  # pragma: allowlist secret
                public_key="pk-test",
                base_url="https://langfuse.example.invalid",
                project_id=None,
            ),
            log_level=log_level,
        ),
    )


class _FakeClient:
    def __init__(self, trace_id: str | None):
        self._trace_id = trace_id
        self.events: list[dict] = []

    def get_current_trace_id(self):
        return self._trace_id

    def create_event(self, *, name, status_message, level):
        self.events.append(
            {"name": name, "status_message": status_message, "level": level}
        )


class TestGetLogger:
    def test_namespaces_under_evals_root(self):
        assert get_logger("adapters.evaluators.base").name == (
            "themefinder.evals.adapters.evaluators.base"
        )

    def test_does_not_double_prefix_an_already_namespaced_name(self):
        name = "themefinder.evals.utils.langfuse"
        assert get_logger(name).name == name


class TestConfigure:
    def test_configures_only_the_evals_logger_not_root(self):
        root_handlers_before = list(logging.getLogger().handlers)

        configure_logging()

        assert logging.getLogger().handlers == root_handlers_before
        evals_logger = logging.getLogger("themefinder.evals")
        assert evals_logger.propagate is False
        assert len(evals_logger.handlers) == 1

    def test_is_idempotent_but_force_reconfigures(self):
        configure_logging()
        configure_logging()
        evals_logger = logging.getLogger("themefinder.evals")
        assert len(evals_logger.handlers) == 1

        configure_logging(force=True)
        assert len(evals_logger.handlers) == 1

    def test_reads_level_from_settings(self, monkeypatch):
        monkeypatch.setattr(
            logging_config,
            "eval_settings",
            make_eval_settings(log_level="DEBUG"),
        )

        configure_logging()

        assert logging.getLogger("themefinder.evals").level == logging.DEBUG

    def test_langfuse_handler_added_only_when_langfuse_active(self, monkeypatch):
        configure_logging()
        assert not any(
            isinstance(h, _LangfuseLogHandler)
            for h in logging.getLogger("themefinder.evals").handlers
        )

        logging_config._configured = False
        logging.getLogger("themefinder.evals").handlers.clear()
        _enable_langfuse(monkeypatch)

        configure_logging()

        langfuse_handlers = [
            h
            for h in logging.getLogger("themefinder.evals").handlers
            if isinstance(h, _LangfuseLogHandler)
        ]
        assert len(langfuse_handlers) == 1
        # No explicit level: the handler follows the logger, so one
        # THEMEFINDER_EVAL_LOG_LEVEL drives both stderr and Langfuse.
        assert langfuse_handlers[0].level == logging.NOTSET

    def test_langfuse_forwards_verbose_records_when_log_level_is_debug(
        self, monkeypatch
    ):
        client = _FakeClient(trace_id="trace-1")
        monkeypatch.setattr("langfuse.get_client", lambda: client)
        _enable_langfuse(monkeypatch, log_level="DEBUG")

        configure_logging()
        logging.getLogger("themefinder.evals").debug("verbose detail")

        assert [e["status_message"] for e in client.events] == ["verbose detail"]

    def test_langfuse_drops_records_below_the_configured_level(self, monkeypatch):
        client = _FakeClient(trace_id="trace-1")
        monkeypatch.setattr("langfuse.get_client", lambda: client)
        _enable_langfuse(monkeypatch, log_level="WARNING")

        configure_logging()
        logging.getLogger("themefinder.evals").info("routine")

        assert client.events == []


class TestHumanFormatter:
    def test_renders_extra_fields_as_key_value(self):
        formatter = _HumanFormatter("%(levelname)s %(name)s %(message)s")
        record = logging.LogRecord(
            name="themefinder.evals.x",
            level=logging.INFO,
            pathname="f.py",
            lineno=1,
            msg="evaluator finished",
            args=None,
            exc_info=None,
        )
        record.eval_type = "generation"
        record.score = 0.91

        out = formatter.format(record)

        assert out.startswith("INFO themefinder.evals.x evaluator finished")
        assert "eval_type=generation" in out
        assert "score=0.91" in out


class TestLangfuseLogHandler:
    def test_forwards_to_active_trace_with_mapped_level(self, monkeypatch):
        client = _FakeClient(trace_id="trace-1")
        monkeypatch.setattr("langfuse.get_client", lambda: client)
        handler = _LangfuseLogHandler()

        handler.emit(
            logging.LogRecord(
                name="themefinder.evals.x",
                level=logging.ERROR,
                pathname="f.py",
                lineno=1,
                msg="boom",
                args=None,
                exc_info=None,
            )
        )

        assert len(client.events) == 1
        assert client.events[0]["level"] == "ERROR"
        assert client.events[0]["name"] == "log:themefinder.evals.x"

    def test_masks_message_and_omits_extra_fields(self, monkeypatch):
        client = _FakeClient(trace_id="trace-1")
        monkeypatch.setattr("langfuse.get_client", lambda: client)
        handler = _LangfuseLogHandler()

        record = logging.LogRecord(
            name="themefinder.evals.x",
            level=logging.WARNING,
            pathname="f.py",
            lineno=1,
            msg="emailed %s",
            args=("user@example.com",),
            exc_info=None,
        )
        record.response_text = "secret response"

        handler.emit(record)

        status = client.events[0]["status_message"]
        assert "user@example.com" not in status
        assert "[redacted]" in status
        assert "secret response" not in status

    def test_no_op_without_active_trace(self, monkeypatch):
        client = _FakeClient(trace_id=None)
        monkeypatch.setattr("langfuse.get_client", lambda: client)
        handler = _LangfuseLogHandler()

        handler.emit(
            logging.LogRecord(
                name="themefinder.evals.x",
                level=logging.WARNING,
                pathname="f.py",
                lineno=1,
                msg="ignored",
                args=None,
                exc_info=None,
            )
        )

        assert client.events == []
