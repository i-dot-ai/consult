"""Response generation using LLM for synthetic consultation datasets."""

import logging
import random
from collections.abc import Callable
from dataclasses import dataclass

import openai
from pydantic import BaseModel, Field

from synthetic.config import NoiseLevel, QuestionConfig, ResponseLength, ResponseType
from synthetic.llm_generators.retry import parse_with_retries
from synthetic.prompts.utils import load_prompt

logger = logging.getLogger(__name__)


class GeneratedResponse(BaseModel):
    """LLM-generated consultation response."""

    response: str = Field(description="The consultation response text")
    sentiment: str = Field(description="AGREE, DISAGREE, or UNCLEAR")
    evidence_rich: bool = Field(
        description="True if response contains specific evidence, examples, or personal experience"
    )


@dataclass
class RespondentSpec:
    """Specification for a single respondent across all questions."""

    response_id: int
    persona: dict[str, str]
    base_disposition: ResponseType  # Overall stance for Q1
    length: ResponseLength
    apply_noise: bool
    noise_type: str | None = None


@dataclass
class PreviousResponse:
    """A previous response in the survey for context."""

    question_text: str
    response_text: str
    sentiment: str


SYSTEM_PROMPT_FIRST_QUESTION = load_prompt("response_first_question_system.md")

SYSTEM_PROMPT_WITH_CONTEXT = load_prompt("response_with_context_system.md")


async def generate_respondent_survey(
    llm: tuple[openai.AsyncOpenAI, str],
    respondent: RespondentSpec,
    questions: list[QuestionConfig],
    themes_by_question: dict[int, list[dict]],
    noise_level: NoiseLevel,
    on_response_complete: Callable[[], None] | None = None,
) -> list[dict]:
    """Generate all responses for a single respondent across all questions.

    Processes questions sequentially, passing previous responses as context
    to maintain consistency in the respondent's viewpoint.

    Args:
        llm: Tuple of (AsyncOpenAI client, deployment name).
        respondent: Respondent specification with persona and base disposition.
        questions: List of question configurations in order.
        themes_by_question: Dict mapping question number to themes list.
        noise_level: Noise injection intensity.
        on_response_complete: Callback invoked when each response finishes.

    Returns:
        List of response dicts, one per question, with all required fields.
    """
    client, deployment = llm

    previous_responses: list[PreviousResponse] = []
    results = []

    for question in questions:
        themes = themes_by_question[question.number]
        is_first_question = len(previous_responses) == 0

        # Select themes for this response
        theme_ids, stances = _select_themes_for_response(
            respondent.base_disposition,
            themes,
            previous_responses,
        )

        # Build prompts
        if is_first_question:
            system_prompt = _build_first_question_prompt(respondent)
        else:
            system_prompt = _build_context_prompt(respondent)

        human_prompt = _build_human_prompt(
            question=question,
            themes=themes,
            theme_ids=theme_ids,
            stances=stances,
            respondent=respondent,
            previous_responses=previous_responses,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": human_prompt},
        ]

        response = await parse_with_retries(
            client=client,
            model=deployment,
            messages=messages,
            response_format=GeneratedResponse,
            reasoning_effort="medium",
            logger=logger,
            operation_name=(
                f"response generation for response_id={respondent.response_id}, "
                f"question={question.number}"
            ),
            extra_retryable_markers=(
                "content_filter",
                "ResponsibleAIPolicyViolation",
            ),
        )

        final_text = response.response
        if respondent.apply_noise and respondent.noise_type:
            final_text = _apply_noise(final_text, respondent.noise_type, noise_level)

        result = {
            "response_id": respondent.response_id,
            "question_number": question.number,
            "response": final_text,
            "position": response.sentiment,
            "evidence_rich": "YES" if response.evidence_rich else "NO",
            "labels": theme_ids,
            "stances": stances,
        }
        results.append(result)

        # Track for next question's context
        previous_responses.append(
            PreviousResponse(
                question_text=question.text,
                response_text=final_text,
                sentiment=response.sentiment,
            )
        )

        if on_response_complete:
            on_response_complete()

    return results


async def generate_respondent_batch(
    llm: tuple[openai.AsyncOpenAI, str],
    respondents: list[RespondentSpec],
    questions: list[QuestionConfig],
    themes_by_question: dict[int, list[dict]],
    noise_level: NoiseLevel,
    on_response_complete: Callable[[], None] | None = None,
) -> list[dict]:
    """Generate responses for a batch of respondents (parallelised across respondents).

    Each respondent processes their questions sequentially for consistency,
    but multiple respondents are processed in parallel.

    Args:
        llm: Tuple of (AsyncOpenAI client, deployment name).
        respondents: List of respondent specifications.
        questions: List of question configurations in order.
        themes_by_question: Dict mapping question number to themes list.
        noise_level: Noise injection intensity.
        on_response_complete: Callback invoked when each response finishes.

    Returns:
        Flat list of all response dicts across all respondents and questions.
    """
    import asyncio

    tasks = [
        asyncio.create_task(
            generate_respondent_survey(
                llm=llm,
                respondent=respondent,
                questions=questions,
                themes_by_question=themes_by_question,
                noise_level=noise_level,
                on_response_complete=on_response_complete,
            )
        )
        for respondent in respondents
    ]

    # Gather all results - return_exceptions=True prevents one failure cancelling all tasks
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out failed respondents and log errors
    successful_results = []
    for i, result in enumerate(all_results):
        if isinstance(result, Exception):
            respondent_id = respondents[i].response_id
            logger.error(
                f"Respondent {respondent_id} failed: {type(result).__name__}: {result}"
            )
        else:
            successful_results.append(result)

    # Flatten: list of lists -> single list
    return [
        response
        for respondent_responses in successful_results
        for response in respondent_responses
    ]


def _select_themes_for_response(
    base_disposition: ResponseType,
    themes: list[dict],
    previous_responses: list[PreviousResponse],
) -> tuple[list[str], list[str]]:
    """Select themes and stances for a response.

    For Q1, uses the base disposition. For subsequent questions,
    infers stance from previous response sentiments for consistency.

    Args:
        base_disposition: The respondent's base response type.
        themes: Available themes for this question.
        previous_responses: Previous responses for context.

    Returns:
        Tuple of (theme_ids, stances).
    """
    if base_disposition == ResponseType.OFF_TOPIC:
        return ["XX"], ["NEUTRAL"]

    if base_disposition == ResponseType.LOW_QUALITY:
        return ["XY"], ["NEUTRAL"]

    # Get regular themes (excluding fallback themes)
    regular_themes = [t for t in themes if t["topic_id"] not in ("XX", "XY")]

    if not regular_themes:
        return ["XX"], ["NEUTRAL"]

    # Select 1-3 themes
    n_themes = random.choice([1, 2, 3])
    n_themes = min(n_themes, len(regular_themes))
    selected = random.sample(regular_themes, n_themes)
    theme_ids = [t["topic_id"] for t in selected]

    # Determine stances based on disposition and previous responses
    if previous_responses:
        # Infer from previous sentiment for consistency
        prev_sentiments = [r.sentiment for r in previous_responses]
        agrees = sum(1 for s in prev_sentiments if s == "AGREE")
        disagrees = sum(1 for s in prev_sentiments if s == "DISAGREE")

        if agrees > disagrees:
            dominant_stance = "POSITIVE"
        elif disagrees > agrees:
            dominant_stance = "NEGATIVE"
        else:
            dominant_stance = "NEUTRAL"

        # Mostly use dominant stance with some variation
        stances = []
        for _ in theme_ids:
            if random.random() < 0.8:
                stances.append(dominant_stance)
            else:
                stances.append(random.choice(["POSITIVE", "NEGATIVE", "NEUTRAL"]))
    else:
        # First question: use base disposition
        if base_disposition == ResponseType.AGREE:
            stances = ["POSITIVE"] * len(theme_ids)
        elif base_disposition == ResponseType.DISAGREE:
            stances = ["NEGATIVE"] * len(theme_ids)
        else:  # NUANCED
            stances = [
                random.choice(["POSITIVE", "NEGATIVE", "NEUTRAL"]) for _ in theme_ids
            ]

    return theme_ids, stances


def _format_persona(persona: dict[str, str]) -> str:
    """Format persona as readable bullet points.

    Args:
        persona: Dict mapping display_name to sampled value.

    Returns:
        Formatted persona string.
    """
    lines = []
    for key, value in persona.items():
        # Clean up display name (remove trailing punctuation like ":")
        clean_key = key.rstrip(":?")
        lines.append(f"- {clean_key}: {value}")
    return "\n".join(lines)


def _build_first_question_prompt(respondent: RespondentSpec) -> str:
    """Build system prompt for the first question."""
    length_range = respondent.length.value
    persona_desc = _format_persona(respondent.persona)

    return SYSTEM_PROMPT_FIRST_QUESTION.format(
        persona_desc=persona_desc,
        min_words=length_range[0],
        max_words=length_range[1],
        response_type=respondent.base_disposition.value,
    )


def _build_context_prompt(respondent: RespondentSpec) -> str:
    """Build system prompt for subsequent questions with context instruction."""
    length_range = respondent.length.value
    persona_desc = _format_persona(respondent.persona)

    return SYSTEM_PROMPT_WITH_CONTEXT.format(
        persona_desc=persona_desc,
        min_words=length_range[0],
        max_words=length_range[1],
    )


def _build_human_prompt(
    question: QuestionConfig,
    themes: list[dict],
    theme_ids: list[str],
    stances: list[str],
    respondent: RespondentSpec,
    previous_responses: list[PreviousResponse],
) -> str:
    """Build human prompt with question, themes, and optional previous context."""
    parts = []

    # Add previous responses context if any
    if previous_responses:
        parts.append("## Your Previous Responses in This Consultation\n")
        for i, prev in enumerate(previous_responses, 1):
            parts.append(f"**Q{i}:** {prev.question_text}")
            parts.append(f'*Your answer ({prev.sentiment}):* "{prev.response_text}"\n')
        parts.append("---\n")

    # Current question
    question_text = question.text
    if question.scale_statement:
        question_text = f'{question.text}\n\nStatement: "{question.scale_statement}"'

    parts.append(f"## Current Question\n{question_text}\n")

    # Theme guidance
    theme_context = []
    for tid, stance in zip(theme_ids, stances):
        theme = next((t for t in themes if t["topic_id"] == tid), None)
        if theme:
            theme_context.append(f"- {theme['topic_label']} (stance: {stance})")

    if theme_context:
        parts.append(
            "Your response should address these themes with the indicated stance:"
        )
        parts.append("\n".join(theme_context))
        parts.append("")

    # Evidence instruction for longer responses
    if respondent.length.value[0] >= 51:
        parts.append(
            "Include specific examples, personal experience, or evidence where appropriate.\n"
        )

    # Consistency reminder for subsequent questions
    if previous_responses:
        parts.append(
            "**Remember:** Stay consistent with your previous responses - maintain your overall viewpoint and concerns."
        )

    parts.append("\nWrite your consultation response now.")

    return "\n".join(parts)


def _apply_noise(text: str, noise_type: str, level: NoiseLevel) -> str:
    """Apply noise injection to response text."""
    intensity = {
        NoiseLevel.LOW: 0.3,
        NoiseLevel.MEDIUM: 0.5,
        NoiseLevel.HIGH: 0.8,
    }[level]

    if noise_type == "typo":
        return _inject_typos(text, intensity)
    elif noise_type == "grammar":
        return _inject_grammar_errors(text, intensity)
    elif noise_type == "caps":
        return text.upper()
    elif noise_type == "emotional":
        return _inject_emotional_language(text)
    elif noise_type == "sarcasm":
        return _add_sarcasm_markers(text)

    return text


def _inject_typos(text: str, intensity: float) -> str:
    """Inject realistic typos into text."""
    words = text.split()
    n_typos = max(1, int(len(words) * intensity * 0.1))

    typo_patterns = [
        lambda w: w[:-1] if len(w) > 3 else w,
        lambda w: w + w[-1] if len(w) > 2 else w,
        lambda w: w[:1] + w[1:].replace("e", "r", 1) if "e" in w[1:] else w,
        lambda w: w.replace("th", "hte", 1) if "th" in w else w,
    ]

    for _ in range(n_typos):
        if words:
            idx = random.randint(0, len(words) - 1)
            pattern = random.choice(typo_patterns)
            words[idx] = pattern(words[idx])

    return " ".join(words)


def _inject_grammar_errors(text: str, intensity: float) -> str:
    """Inject grammar errors into text."""
    if intensity > 0.5:
        text = text.replace(",", "", 1)

    if intensity > 0.7:
        replacements = [
            ("there is", "theres"),
            ("they are", "their"),
            ("should have", "should of"),
            ("could have", "could of"),
        ]
        for old, new in replacements:
            if old in text.lower():
                text = text.replace(old, new, 1)
                break

    return text


def _inject_emotional_language(text: str) -> str:
    """Add emotional emphasis to text."""
    emphatics = [
        "Absolutely ",
        "I really think ",
        "It's outrageous that ",
        "I strongly believe ",
    ]

    if not text[0].isupper():
        text = text[0].upper() + text[1:]

    prefix = random.choice(emphatics)
    text = prefix.lower() + text[0].lower() + text[1:]

    if text.endswith("."):
        text = text[:-1] + "!"

    return text


def _add_sarcasm_markers(text: str) -> str:
    """Add sarcasm indicators to text."""
    sarcastic_additions = [
        " (as if that will ever happen)",
        " - what a surprise",
        " Obviously...",
    ]

    sentences = text.split(". ")
    if len(sentences) > 1:
        idx = random.randint(0, len(sentences) - 2)
        sentences[idx] += random.choice(sarcastic_additions)
        text = ". ".join(sentences)

    return text
