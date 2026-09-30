"""Logging setup for the evals ports-and-adapters tree."""

import logging
import sys

from settings import get_settings

_configured = False


class _HumanFormatter(logging.Formatter):
    """Human-readable line + `extra` fields as key=value; unredacted (Langfuse-only masking)."""

    _RESERVED = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self._RESERVED
        }
        if extras:
            base += " " + " ".join(f"{key}={value}" for key, value in extras.items())
        return base


class _LangfuseLogHandler(logging.Handler):
    """Forward records to the active Langfuse trace as events."""

    _LEVEL_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "DEFAULT",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "ERROR",
    }

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from langfuse import get_client

            client = get_client()
            if client.get_current_trace_id() is None:
                return
            client.create_event(
                name=f"log:{record.name}",
                status_message=self.format(record),
                level=self._LEVEL_MAP.get(record.levelno, "DEFAULT"),
            )
        except Exception:
            self.handleError(record)


def configure_logging(*, force: bool = False) -> None:
    """Configure the `themefinder.evals` logger. Idempotent unless `force`."""
    global _configured
    if _configured and not force:
        return

    settings = get_settings()
    logger = logging.getLogger("themefinder.evals")
    logger.handlers.clear()
    logger.setLevel(settings.log_level)
    logger.propagate = False

    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(
        _HumanFormatter(
            "%(asctime)s %(levelname)-7s %(name)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(stream)

    if settings.active_langfuse is not None:
        logger.addHandler(_LangfuseLogHandler())

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a `themefinder.evals.*` logger, configuring the tree on first use."""
    configure_logging()
    if name == "themefinder.evals" or name.startswith("themefinder.evals."):
        return logging.getLogger(name)
    return logging.getLogger(f"themefinder.evals.{name}")
