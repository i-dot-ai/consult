"""Theme generation using LLM for synthetic consultation datasets.

Uses fan-out parallelisation (10 calls) for diverse theme discovery,
then consolidates with light-touch rationalisation.
"""

import asyncio
import logging
from collections.abc import Callable

import openai
from pydantic import BaseModel, Field, ValidationError

from synthetic.config import DRAFTING_MODEL, DemographicField
from synthetic.prompts.utils import load_prompt

logger = logging.getLogger(__name__)

# Number of parallel theme generation calls for diversity
FAN_OUT_COUNT = 10

# Retry configuration for transient LLM errors
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0


class Theme(BaseModel):
    """Single theme definition for structured output."""

    topic_id: str = Field(
        description="Theme identifier (A-Z, then AA-AZ for extended sets)"
    )
    topic_label: str = Field(description="Short theme name (2-5 words)")
    topic_description: str = Field(
        description="Concise description of what responses in this theme argue (15-25 words max)"
    )


class ThemeSet(BaseModel):
    """Complete theme set returned by the LLM."""

    themes: list[Theme]


THEME_GENERATION_BACKGROUND = load_prompt("theme_generation_system.md")
THEME_GENERATION_TASK = load_prompt("theme_generation_user.md")

CONSOLIDATION_SYSTEM_PROMPT = load_prompt("theme_consolidation_system.md")


def _generate_topic_ids(n: int) -> list[str]:
    """Generate topic IDs for n themes.

    Uses A-Z for first 26, then AA-AZ, BA-BZ, etc.

    Args:
        n: Number of IDs needed.

    Returns:
        List of topic ID strings.
    """
    ids = []
    for i in range(n):
        if i < 26:
            ids.append(chr(65 + i))  # A-Z
        else:
            # AA, AB, ..., AZ, BA, BB, ...
            first = chr(65 + ((i - 26) // 26))
            second = chr(65 + ((i - 26) % 26))
            ids.append(first + second)
    return ids


async def generate_themes(
    client: openai.AsyncOpenAI,
    topic: str,
    question: str,
    demographic_fields: list[DemographicField],
    on_fan_out_complete: Callable[[], None] | None = None,
) -> list[dict]:
    """Generate comprehensive themes for a consultation question.

    Uses fan-out parallelisation: 10 concurrent LLM calls generate diverse themes,
    then a consolidation step deduplicates and rationalises them.

    Args:
        topic: Overall consultation topic.
        question: Specific question text.
        demographic_fields: Enabled demographic fields for perspective consideration.
        on_fan_out_complete: Callback invoked after each fan-out call completes.

    Returns:
        List of theme dicts with topic_id, topic_label, topic_description, topic.
    """
    raw_themes = await _fan_out_theme_generation(
        client=client,
        topic=topic,
        question=question,
        demographic_fields=demographic_fields,
        on_complete=on_fan_out_complete,
    )

    consolidated_themes = await _consolidate_themes(
        client=client,
        raw_themes=raw_themes,
        topic=topic,
        question=question,
    )

    # XX and XY are used as fixed fallback IDs — safe since the sequential generator
    # would need 650+ themes to reach them
    consolidated_themes.extend(
        [
            {
                "topic_id": "XX",
                "topic_label": "None of the Above",
                "topic_description": "Response discusses a topic not covered by listed themes",
                "topic": "None of the Above: Response discusses a topic not covered by listed themes",
            },
            {
                "topic_id": "XY",
                "topic_label": "No Reason Given",
                "topic_description": "Response does not provide a substantive answer",
                "topic": "No Reason Given: Response does not provide a substantive answer",
            },
        ]
    )

    return consolidated_themes


async def _fan_out_theme_generation(
    client: openai.AsyncOpenAI,
    topic: str,
    question: str,
    demographic_fields: list[DemographicField],
    on_complete: Callable[[], None] | None = None,
) -> list[dict]:
    """Generate themes with fan-out parallelisation.

    Runs FAN_OUT_COUNT concurrent LLM calls to discover diverse themes.

    Args:
        topic: Consultation topic.
        question: Question text.
        demographic_fields: Demographic fields for context.
        on_complete: Callback for each completed call.

    Returns:
        Combined list of all themes from all calls (with duplicates).
    """
    demographic_context = _build_demographic_context(demographic_fields)

    human_prompt = THEME_GENERATION_TASK.format(
        topic=topic,
        question=question,
        demographic_context=demographic_context,
    )

    messages = [
        {"role": "system", "content": THEME_GENERATION_BACKGROUND},
        {"role": "user", "content": human_prompt},
    ]

    async def single_call(call_id: int) -> list[dict]:
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                result = (
                    (
                        await client.beta.chat.completions.parse(
                            model=DRAFTING_MODEL,
                            messages=messages,
                            response_format=ThemeSet,
                            reasoning_effort="medium",
                        )
                    )
                    .choices[0]
                    .message.parsed
                )
                themes = [
                    {
                        "topic_label": t.topic_label,
                        "topic_description": t.topic_description,
                    }
                    for t in result.themes
                ]
                if on_complete:
                    on_complete()
                return themes
            except Exception as e:
                last_error = e
                error_type = type(e).__name__

                is_validation_error = isinstance(e, ValidationError)
                is_connection_error = (
                    "ECONNRESET" in str(e)
                    or "ENOTFOUND" in str(e)
                    or "ECONNREFUSED" in str(e)
                    or "DNS" in str(e)
                    or "connection" in str(e).lower()
                )

                if is_validation_error or is_connection_error:
                    if attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAY_SECONDS * (2**attempt)
                        logger.warning(
                            f"Retryable error ({error_type}) in theme fan-out call {call_id}, "
                            f"attempt {attempt + 1}/{MAX_RETRIES}. Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        continue
                raise

        raise last_error  # type: ignore[misc]

    tasks = [asyncio.create_task(single_call(i)) for i in range(FAN_OUT_COUNT)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_themes = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(
                f"Theme fan-out call {i} failed: {type(result).__name__}: {result}"
            )
        else:
            all_themes.extend(result)

    if not all_themes:
        raise RuntimeError("All theme generation calls failed")

    return all_themes


async def _consolidate_themes(
    client: openai.AsyncOpenAI,
    raw_themes: list[dict],
    topic: str,
    question: str,
) -> list[dict]:
    """Consolidate and deduplicate themes from fan-out generation.

    Uses a light-touch LLM call to merge duplicates while preserving diversity.

    Args:
        raw_themes: Combined themes from all fan-out calls.
        topic: Consultation topic.
        question: Question text.

    Returns:
        Deduplicated and rationalised theme list.
    """
    themes_text = "\n".join(
        f"- {t['topic_label']}: {t['topic_description']}" for t in raw_themes
    )

    human_prompt = f"""## Consultation Context
Topic: {topic}
Question: {question}

## Raw Themes to Consolidate
The following {len(raw_themes)} themes were generated from multiple parallel analyses.
Consolidate them by removing duplicates and merging highly similar themes.

{themes_text}

## Your Task
1. Remove exact or near-duplicate themes
2. Merge themes that express essentially the same viewpoint
3. Preserve distinct minority viewpoints - don't over-consolidate
4. Output a clean, deduplicated theme list

Be CONSERVATIVE - when in doubt, keep themes separate. Diversity is valuable."""

    messages = [
        {"role": "system", "content": CONSOLIDATION_SYSTEM_PROMPT},
        {"role": "user", "content": human_prompt},
    ]

    result = None
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            result = (
                (
                    await client.beta.chat.completions.parse(
                        model=DRAFTING_MODEL,
                        messages=messages,
                        response_format=ThemeSet,
                        reasoning_effort="low",
                    )
                )
                .choices[0]
                .message.parsed
            )
            break
        except Exception as e:
            last_error = e
            error_type = type(e).__name__

            is_validation_error = isinstance(e, ValidationError)
            is_connection_error = (
                "ECONNRESET" in str(e)
                or "ENOTFOUND" in str(e)
                or "ECONNREFUSED" in str(e)
                or "DNS" in str(e)
                or "connection" in str(e).lower()
            )

            if is_validation_error or is_connection_error:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_SECONDS * (2**attempt)
                    logger.warning(
                        f"Retryable error ({error_type}) in theme consolidation, "
                        f"attempt {attempt + 1}/{MAX_RETRIES}. Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    continue
            raise

    if result is None:
        raise last_error  # type: ignore[misc]

    topic_ids = _generate_topic_ids(len(result.themes))

    themes = [
        {
            "topic_id": topic_ids[i],
            "topic_label": t.topic_label,
            "topic_description": t.topic_description,
            "topic": f"{t.topic_label}: {t.topic_description}",
        }
        for i, t in enumerate(result.themes)
    ]

    return themes


def _build_demographic_context(fields: list[DemographicField]) -> str:
    """Build demographic context string for the prompt.

    Args:
        fields: List of demographic fields (enabled ones).

    Returns:
        Formatted string describing demographic dimensions.
    """
    enabled = [f for f in fields if f.enabled]

    if not enabled:
        return "No specific demographic dimensions tracked - consider general UK population diversity."

    lines = []
    for field in enabled:
        values_str = ", ".join(field.values)
        lines.append(f"- **{field.display_name}**: {values_str}")

    return "\n".join(lines)
