"""Prompt templates for generation evaluation."""

GENERATION_EVAL = """You are an expert in natural language processing and topic modelling. Your task is to evaluate how well topics in LIST 1 are captured by topics in LIST 2.

For each topic in LIST 1, find the best matching topic in LIST 2 and assign one of three decisions:

- **STRONG**: The topics represent the same core concept, even if worded differently.
- **PARTIAL**: The topics are related but differ in scope, specificity, or emphasis.
- **NO**: No meaningful match exists in LIST 2.

For each topic, provide:
1. The label of the best matching topic in LIST 2 (or "none" if NO match)
2. Your decision (STRONG, PARTIAL, or NO)
3. A brief reasoning (1-2 sentences) explaining your decision

## Calibration Examples

These examples illustrate the expected standard for each decision:

**STRONG** — "Humiliating current system" ↔ "Inhumane current assessments"
Reasoning: Both topics describe the degrading nature of the existing assessment process. Different wording, same core concept.

**PARTIAL** — "Speeding up the process" ↔ "Dignified assessments"
Reasoning: Both relate to improving the assessment experience, but one focuses on speed while the other focuses on dignity. Related but different emphasis.

**NO** — "Better job matching" ↔ "Reduction in administrative burden"
Reasoning: Job matching and administrative burden are entirely different concerns with no conceptual overlap.

## Output Format

Return strict JSON in this format:
{{
    "evaluations": {{
        "topic_label_from_list_1": {{
            "matched_to": "topic_label_from_list_2 or none",
            "decision": "STRONG or PARTIAL or NO",
            "reasoning": "Brief explanation"
        }}
    }}
}}

LIST 1:
{topic_list_1}

LIST 2:
{topic_list_2}"""

TITLE_SPECIFICITY_EVAL = """You are an expert in evaluating the quality of topic labels from a topic modelling system. Your task is to assess whether each theme title is specific enough to convey meaningful information, or whether it is too vague to be useful.

For each theme title, assign one of two decisions:

- **SPECIFIC**: The title conveys a clear, concrete concept that distinguishes it from other themes. A reader could understand the topic's focus from the title alone.
- **VAGUE**: The title is generic, ambiguous, or could apply to many different topics. It fails to communicate what makes this theme distinct.

## Calibration Examples

**VAGUE**: "Concerns about the process"
Reasoning: Too generic — almost any negative theme could be described as "concerns about the process."

**SPECIFIC**: "Delays in planning permission approvals"
Reasoning: Clearly identifies both the issue (delays) and the context (planning permission approvals).

**VAGUE**: "General support"
Reasoning: Does not specify what is being supported or why.

**SPECIFIC**: "Mandatory disability awareness training for assessors"
Reasoning: Identifies a concrete policy recommendation with clear scope.

## Output Format

Return strict JSON in this format:
{{
    "evaluations": {{
        "theme_title_1": {{
            "decision": "SPECIFIC or VAGUE",
            "reasoning": "Brief explanation"
        }}
    }}
}}

THEME TITLES:
{theme_titles}"""


def generation_eval_prompt(
    topic_list_1: list[dict] | dict,
    topic_list_2: list[dict] | dict,
) -> str:
    """Generate a prompt for comparing two topic lists."""
    return GENERATION_EVAL.format(
        topic_list_1=topic_list_1,
        topic_list_2=topic_list_2,
    )


def title_specificity_eval_prompt(theme_titles: list[str]) -> str:
    """Generate a prompt for theme-title specificity evaluation."""
    return TITLE_SPECIFICITY_EVAL.format(theme_titles=theme_titles)
