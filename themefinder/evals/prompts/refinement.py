"""Prompt template for refinement evaluation."""

REFINEMENT_EVAL = """You are an expert in natural language processing and topic modelling. Your task is to evaluate how well a model refines topic labels and descriptions. You will be shown:

1. ORIGINAL TOPICS: The topics before refinement.
2. NEW TOPICS: The topics after a refinement step that improves labels and descriptions.

Evaluate the NEW TOPICS based on the ORIGINAL TOPICS on three criteria, each scored from 0 to 5:

## Information Retention

How well do the NEW TOPICS preserve key information from the ORIGINAL TOPICS?

- 5: All important details retained, nothing meaningful lost
- 4: Most important information preserved, only minor details lost
- 3: Core concepts preserved but significant details lost
- 2: Important information missing from refined topics
- 1: Most key information lost during refinement
- 0: Essential information completely lost

## Response References

Do the NEW TOPICS avoid language that references survey responses directly? Topics should describe the content itself, not how respondents expressed it.

- 5: No topics use language that refers to responses (e.g. "respondents said", "the majority of responses")
- 4: At most one topic contains a minor response reference
- 3: A few topics reference responses but most are content-focused
- 2: Many topics refer to responses rather than describing content directly
- 1: Most topics are framed around what respondents said
- 0: Nearly all topics reference responses instead of describing content

## Distinctiveness

How well do the NEW TOPICS represent distinct concepts without overlap?

- 5: All topics are clearly distinct with no conceptual overlap
- 4: Nearly all distinct, one or two minor overlaps
- 3: Most distinct but some noticeable overlap between topics
- 2: Several topics overlap significantly
- 1: Most topics overlap or are poorly differentiated
- 0: Topics are largely redundant or indistinguishable

## Calibration Examples

**High quality refinement** (information_retention: 5, response_references: 5, distinctiveness: 4):
Original topic: "People saying they want better access to services". Refined to: "Service accessibility gaps: Limited availability of essential services in rural and underserved areas creates barriers to healthcare, education, and social support." The refined version removes the response reference ("people saying"), adds a specific label, and expands the description with concrete detail. One minor overlap exists with another topic about healthcare specifically.

**Poor refinement** (information_retention: 2, response_references: 1, distinctiveness: 3):
Original topic: "Concerns about environmental regulations being too strict". Refined to: "Many respondents feel regulations are problematic: The majority of responses indicate that current rules are seen as excessive by participants." The refined version loses the environmental specificity, introduces multiple response references, and overlaps with other concerns about regulation.

## Instructions

1. First, reason about how the refinement performed on each criterion.
2. Then provide your scores in strict JSON format.

Return only the following JSON, no other text:

{{
  "information_retention": <score 0-5>,
  "information_retention_reasoning": "1-2 sentence explanation",
  "response_references": <score 0-5>,
  "response_references_reasoning": "1-2 sentence explanation",
  "distinctiveness": <score 0-5>,
  "distinctiveness_reasoning": "1-2 sentence explanation"
}}

ORIGINAL TOPICS:
{original_topics}

NEW TOPICS:
{new_topics}
"""


def refinement_eval_prompt(
    original_topics: list[dict],
    new_topics: list[dict],
) -> str:
    """Generate a prompt for refinement evaluation."""
    return REFINEMENT_EVAL.format(
        original_topics=original_topics,
        new_topics=new_topics,
    )


CLARITY_EVAL = """You are evaluating whether one refined theme is simple and clear.

Assess only the wording of the theme label and description. PASS when together they
communicate the theme's meaning in simple, clear language that is easy to understand.
FAIL when the wording is confusing, unnecessarily complex, ambiguous, or otherwise
difficult to understand.

Do not assess information retention, response references, distinctiveness, length, or
whether this theme is better than any other theme.

## Refined theme

Label: {topic_label}
Description: {topic_description}

Return only a JSON object in exactly this shape, with no Markdown fences or other text:

{{
  "decision": "PASS" | "FAIL",
  "reasoning": "A brief explanation of the decision."
}}
"""


def clarity_eval_prompt(topic_label: str, topic_description: str) -> str:
    """Generate a clarity-evaluation prompt for one refined theme."""
    return CLARITY_EVAL.format(
        topic_label=topic_label,
        topic_description=topic_description,
    )
