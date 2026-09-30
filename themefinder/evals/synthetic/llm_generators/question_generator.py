"""Question generation using LLM for synthetic consultation datasets.

Generates UK government-style consultation questions following Cabinet Office
principles and the Gunning Principles for fair consultation.
"""

import logging

import openai
from pydantic import BaseModel, Field

from synthetic.config import DRAFTING_MODEL
from synthetic.llm_generators.retry import parse_with_retries
from synthetic.prompts.utils import load_prompt

logger = logging.getLogger(__name__)


class GeneratedQuestion(BaseModel):
    """A single generated consultation question."""

    question_text: str = Field(
        description="The main question text, written in plain English"
    )
    question_type: str = Field(
        description="One of: open_ended, agree_disagree, yes_no, multiple_choice"
    )
    scale_statement: str | None = Field(
        default=None,
        description="For agree_disagree type: the statement respondents rate on a 5-point scale",
    )
    multi_choice_options: list[str] | None = Field(
        default=None,
        description="For multiple_choice type: the options to select from",
    )
    rationale: str = Field(
        description="Brief explanation of why this question is valuable for the consultation"
    )


class QuestionSet(BaseModel):
    """Set of generated consultation questions."""

    questions: list[GeneratedQuestion]


SYSTEM_PROMPT = load_prompt("question_generation_system.md")


async def generate_questions(
    client: openai.AsyncOpenAI,
    topic: str,
    n_questions: int,
    existing_questions: list[str] | None = None,
    feedback: str | None = None,
) -> list[GeneratedQuestion]:
    """Generate consultation questions for a policy topic.

    Args:
        topic: The policy topic for the consultation.
        n_questions: Number of questions to generate.
        existing_questions: Previously approved questions (to avoid duplication).
        feedback: User feedback on previously rejected questions.

    Returns:
        List of GeneratedQuestion objects.
    """
    # Build context about existing questions
    existing_context = ""
    if existing_questions:
        existing_list = "\n".join(f"- {q}" for q in existing_questions)
        existing_context = f"""
## Already Approved Questions (do not duplicate these themes)
{existing_list}
"""

    # Build feedback context
    feedback_context = ""
    if feedback:
        feedback_context = f"""
## Feedback on Previous Suggestions
The user provided this feedback: {feedback}

Take this feedback into account when generating new questions.
"""

    human_prompt = f"""Generate {n_questions} consultation question(s) for the following UK government consultation topic.

## Consultation Topic
{topic}
{existing_context}{feedback_context}
## Requirements
1. Generate exactly {n_questions} question(s)
2. Use a variety of question types appropriate to the topic
3. Start with broader questions, then get more specific
4. Ensure questions are distinct and cover different aspects of the topic
5. Follow UK government consultation best practices
6. Use plain English accessible to the general public

For each question, provide:
- The question text
- The question type (open_ended, agree_disagree, yes_no, or multiple_choice)
- For agree_disagree: include the scale_statement
- For multiple_choice: include the options
- A brief rationale explaining why this question is valuable"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": human_prompt},
    ]

    result = await parse_with_retries(
        client=client,
        model=DRAFTING_MODEL,
        messages=messages,
        response_format=QuestionSet,
        reasoning_effort="high",
        logger=logger,
        operation_name="question generation",
    )
    return result.questions


async def regenerate_single_question(
    client: openai.AsyncOpenAI,
    topic: str,
    rejected_question: str,
    feedback: str,
    existing_questions: list[str],
) -> GeneratedQuestion:
    """Regenerate a single question based on user feedback.

    Args:
        client: OpenAI client (gateway-routed).
        topic: The policy topic for the consultation.
        rejected_question: The question that was rejected.
        feedback: User's feedback on why it was rejected.
        existing_questions: Other approved questions to avoid duplication.

    Returns:
        A new GeneratedQuestion.
    """
    existing_list = (
        "\n".join(f"- {q}" for q in existing_questions)
        if existing_questions
        else "None yet"
    )

    human_prompt = f"""Generate a replacement consultation question for a UK government consultation.

## Consultation Topic
{topic}

## Rejected Question
{rejected_question}

## User Feedback
{feedback}

## Already Approved Questions (avoid duplicating)
{existing_list}

Generate ONE new question that:
1. Addresses the user's feedback
2. Covers a different angle or aspect than the rejected question
3. Doesn't duplicate existing approved questions
4. Follows UK government consultation best practices"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": human_prompt},
    ]

    return await parse_with_retries(
        client=client,
        model=DRAFTING_MODEL,
        messages=messages,
        response_format=GeneratedQuestion,
        reasoning_effort="high",
        logger=logger,
        operation_name="single question regeneration",
    )


class DatasetName(BaseModel):
    """Generated dataset name."""

    name: str = Field(
        description="Short, descriptive dataset name using snake_case (e.g., 'bbc_charter_review', 'housing_policy_2025')"
    )


async def generate_dataset_name(
    client: openai.AsyncOpenAI,
    topic: str,
    questions: list[str],
) -> str:
    """Generate a short, descriptive dataset name from the consultation topic and questions.

    Args:
        client: OpenAI client (gateway-routed).
        topic: The consultation topic (can be long document).
        questions: List of approved question texts.

    Returns:
        Short snake_case dataset name suitable for file paths.
    """
    # Truncate topic if very long (just use first 2000 chars for context)
    topic_excerpt = topic[:2000] + "..." if len(topic) > 2000 else topic

    questions_list = "\n".join(
        f"- {q[:100]}..." if len(q) > 100 else f"- {q}" for q in questions[:10]
    )

    human_prompt = f"""Generate a short, descriptive name for this consultation dataset.

## Topic/Context
{topic_excerpt}

## Questions (first 10)
{questions_list}

## Requirements
- Use snake_case (lowercase with underscores)
- Keep it SHORT: 2-4 words, max 30 characters
- Make it descriptive of the policy area
- Examples: "bbc_charter_review", "housing_reform_2025", "nhs_workforce_plan"

Generate ONE dataset name."""

    messages = [
        {
            "role": "system",
            "content": "You generate short, descriptive dataset names for UK government consultations.",
        },
        {"role": "user", "content": human_prompt},
    ]

    result = await parse_with_retries(
        client=client,
        model=DRAFTING_MODEL,
        messages=messages,
        response_format=DatasetName,
        reasoning_effort="high",
        logger=logger,
        operation_name="dataset name generation",
    )

    # Sanitise the name to ensure it's filesystem-safe
    name = result.name.lower().strip()
    name = name.replace(" ", "_").replace("-", "_")
    name = "".join(c for c in name if c.isalnum() or c == "_")
    name = name[:30]  # Hard limit

    return name if name else "consultation_dataset"
