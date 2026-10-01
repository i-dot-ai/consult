"""Shared retry logic for synthetic LLM generator parse calls."""

import asyncio
import logging
from collections.abc import Iterable
from typing import TypeVar

import openai
from pydantic import BaseModel, ValidationError

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0

T = TypeVar("T", bound=BaseModel)

_RETRYABLE_ERROR_MARKERS = (
    "econnreset",
    "enotfound",
    "econnrefused",
    "dns",
    "connection",
)


def _is_retryable_error(
    error: Exception,
    extra_retryable_markers: Iterable[str] = (),
) -> bool:
    """Return whether an error should trigger a retry."""
    if isinstance(error, ValidationError):
        return True

    error_str = str(error).lower()
    retryable_markers = (
        *_RETRYABLE_ERROR_MARKERS,
        *(marker.lower() for marker in extra_retryable_markers),
    )
    return any(marker in error_str for marker in retryable_markers)


async def parse_with_retries(
    *,
    client: openai.AsyncOpenAI,
    model: str,
    messages: list[dict[str, str]],
    response_format: type[T],
    reasoning_effort: str,
    logger: logging.Logger,
    operation_name: str,
    extra_retryable_markers: Iterable[str] = (),
) -> T:
    """Parse a structured LLM response with retries for transient failures."""
    for attempt in range(MAX_RETRIES):
        try:
            return (
                (
                    await client.beta.chat.completions.parse(
                        model=model,
                        messages=messages,
                        response_format=response_format,
                        reasoning_effort=reasoning_effort,
                    )
                )
                .choices[0]
                .message.parsed
            )
        except Exception as error:
            if _is_retryable_error(error, extra_retryable_markers) and attempt < (
                MAX_RETRIES - 1
            ):
                delay = RETRY_DELAY_SECONDS * (2**attempt)
                logger.warning(
                    "Retryable error (%s) in %s, attempt %s/%s. Retrying in %.1fs...",
                    type(error).__name__,
                    operation_name,
                    attempt + 1,
                    MAX_RETRIES,
                    delay,
                )
                await asyncio.sleep(delay)
                continue
            raise
