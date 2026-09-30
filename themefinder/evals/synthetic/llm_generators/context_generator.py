"""Policy context field generation using LLM for synthetic consultation datasets.

Generates policy-specific respondent context questions (e.g., "Do you have a student loan?")
based on the consultation topic. These complement fixed demographics with topic-relevant
characteristics that influence how respondents answer.
"""

import logging
import openai
from pydantic import BaseModel, Field

from synthetic.config import DRAFTING_MODEL, DemographicField, QuestionConfig
from synthetic.llm_generators.retry import parse_with_retries
from synthetic.prompts.utils import load_prompt

logger = logging.getLogger(__name__)


class ContextFieldOption(BaseModel):
    """Single option for a context field."""

    value: str = Field(description="The option text (e.g., 'Yes - currently repaying')")
    distribution_percent: float = Field(
        description="Estimated UK population percentage (0-100)"
    )
    stance_influence: float = Field(
        description="How this option affects stance: -0.1 (oppose) to +0.1 (support), 0 for neutral"
    )


class GeneratedContextField(BaseModel):
    """LLM-generated policy context field."""

    name: str = Field(
        description="Internal identifier (snake_case, e.g., 'student_loan_status')"
    )
    question_text: str = Field(
        description="Question as it would appear in a survey (e.g., 'Do you currently have a student loan?')"
    )
    options: list[ContextFieldOption] = Field(
        description="Available response options with distributions and stance influences"
    )
    rationale: str = Field(
        description="Brief explanation of why this context is relevant to the policy"
    )


class ContextFieldSet(BaseModel):
    """Complete set of generated context fields."""

    fields: list[GeneratedContextField]


SYSTEM_PROMPT = load_prompt("context_generation_system.md")


async def generate_context_fields(
    client: openai.AsyncOpenAI,
    topic: str,
    questions: list[QuestionConfig],
    n_fields: int = 4,
) -> list[DemographicField]:
    """Generate policy-specific context fields using LLM.

    Args:
        topic: Consultation topic.
        questions: List of consultation questions (for context).
        n_fields: Target number of context fields to generate (3-5).

    Returns:
        List of DemographicField objects with is_policy_context=True.
    """
    # Format questions for context
    questions_text = "\n".join(f"{q.number}. {q.text}" for q in questions)

    human_prompt = f"""Generate {n_fields} policy-specific context questions for this UK government consultation.

## Consultation Topic
{topic}

## Consultation Questions
{questions_text}

## Your Task
1. Identify 3-5 respondent characteristics that are DIRECTLY RELEVANT to this policy
2. For each, create a survey question with realistic UK population distributions
3. Estimate subtle stance influences for each option (±0.1 max)
4. Explain why each context is relevant

Focus on characteristics that would genuinely affect how someone views this policy.
Avoid generic demographics (age, region, etc.) - those are handled separately."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": human_prompt},
    ]

    result = await parse_with_retries(
        client=client,
        model=DRAFTING_MODEL,
        messages=messages,
        response_format=ContextFieldSet,
        reasoning_effort="medium",
        logger=logger,
        operation_name="context field generation",
    )

    # Convert to DemographicField objects
    demographic_fields = []
    for gen_field in result.fields:
        # Normalise distributions to sum to 1.0
        total_pct = sum(opt.distribution_percent for opt in gen_field.options)
        distribution = [
            opt.distribution_percent / total_pct for opt in gen_field.options
        ]

        demographic_fields.append(
            DemographicField(
                name=gen_field.name,
                display_name=gen_field.question_text,
                values=[opt.value for opt in gen_field.options],
                distribution=distribution,
                enabled=True,
                is_policy_context=True,
                stance_modifiers=[opt.stance_influence for opt in gen_field.options],
            )
        )

    return demographic_fields


async def regenerate_context_fields(
    client: openai.AsyncOpenAI,
    topic: str,
    questions: list[QuestionConfig],
    feedback: str,
    n_fields: int = 4,
) -> list[DemographicField]:
    """Regenerate context fields based on user feedback.

    Args:
        client: OpenAI client (gateway-routed).
        topic: Consultation topic.
        questions: List of consultation questions.
        feedback: User's feedback on what to change.
        n_fields: Target number of context fields.

    Returns:
        List of regenerated DemographicField objects.
    """
    questions_text = "\n".join(f"{q.number}. {q.text}" for q in questions)

    human_prompt = f"""Regenerate policy-specific context questions for this UK government consultation,
taking into account the user's feedback.

## Consultation Topic
{topic}

## Consultation Questions
{questions_text}

## User Feedback
{feedback}

## Your Task
Generate {n_fields} improved context questions that address the feedback.
Focus on characteristics directly relevant to this policy."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": human_prompt},
    ]

    result = await parse_with_retries(
        client=client,
        model=DRAFTING_MODEL,
        messages=messages,
        response_format=ContextFieldSet,
        reasoning_effort="medium",
        logger=logger,
        operation_name="context regeneration",
    )

    # Convert to DemographicField objects
    demographic_fields = []
    for gen_field in result.fields:
        total_pct = sum(opt.distribution_percent for opt in gen_field.options)
        distribution = [
            opt.distribution_percent / total_pct for opt in gen_field.options
        ]

        demographic_fields.append(
            DemographicField(
                name=gen_field.name,
                display_name=gen_field.question_text,
                values=[opt.value for opt in gen_field.options],
                distribution=distribution,
                enabled=True,
                is_policy_context=True,
                stance_modifiers=[opt.stance_influence for opt in gen_field.options],
            )
        )

    return demographic_fields
