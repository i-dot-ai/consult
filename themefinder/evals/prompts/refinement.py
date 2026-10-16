"""Prompt template for refinement evaluation."""

import json

REFINEMENT_EVAL = """You are an expert in natural language processing and topic modelling. Your task is to evaluate how well a model refines topic labels and descriptions. You will be shown:

1. ORIGINAL TOPICS: The topics before refinement.
2. NEW TOPICS: The topics after a refinement step that improves labels and descriptions.

Evaluate the NEW TOPICS on three criteria, each scored from 0 to 5:

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

## Fluency

Are the NEW TOPICS well structured with clear labels and informative descriptions?

- 5: All topics have concise, descriptive labels followed by detailed descriptions that expand on (not repeat) the label
- 4: Most topics are well structured with clear labels and good descriptions
- 3: Topics are generally readable but some labels are vague or descriptions merely repeat the label
- 2: Several topics have poor labels or uninformative descriptions
- 1: Most topics are poorly worded or structured
- 0: Topics are unreadable or incomprehensible

## Calibration Examples

**High quality refinement** (response_references: 5, distinctiveness: 4, fluency: 5):
Original topic: "People saying they want better access to services". Refined to: "Service accessibility gaps: Limited availability of essential services in rural and underserved areas creates barriers to healthcare, education, and social support." The refined version removes the response reference ("people saying"), adds a specific label, and expands the description with concrete detail. One minor overlap exists with another topic about healthcare specifically.

**Poor refinement** (response_references: 1, distinctiveness: 3, fluency: 2):
Original topic: "Concerns about environmental regulations being too strict". Refined to: "Many respondents feel regulations are problematic: The majority of responses indicate that current rules are seen as excessive by participants." The refined version introduces multiple response references, and the description merely restates the label.

## Instructions

1. First, reason about how the refinement performed on each criterion.
2. Then provide your scores in strict JSON format.

Return only the following JSON, no other text:

{{
  "response_references": <score 0-5>,
  "response_references_reasoning": "1-2 sentence explanation",
  "distinctiveness": <score 0-5>,
  "distinctiveness_reasoning": "1-2 sentence explanation",
  "fluency": <score 0-5>,
  "fluency_reasoning": "1-2 sentence explanation"
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


INFORMATION_EQUIVALENCE_MATCH_EVAL = """You are evaluating whether two
consultation themes express the same information.

Compare the THEME TO MATCH with the CANDIDATE THEMES. Return YES only if
exactly one candidate theme preserves all material information in the theme to
match, including its subject, claim, scope, qualifiers, and sentiment or
position. Different wording is acceptable.

Return NO if no candidate matches, if more than one candidate matches, if the
candidate is only related, broader, narrower, or contradictory, or if the
information is split across multiple candidates.

Return only the following JSON, with no other text:

{{
  "decision": "YES",
  "matched_candidate_id": 1
}}

For a NO decision, set `matched_candidate_id` to null.

THEME TO MATCH:
{theme_to_match}

CANDIDATE THEMES:
{candidate_themes}
"""


def information_equivalence_match_prompt(
    theme_to_match: str,
    candidate_themes: list[str],
) -> str:
    """Generate a binary element-to-list information-equivalence prompt."""
    numbered_candidate_themes = [
        {"id": index, "theme": theme}
        for index, theme in enumerate(candidate_themes, start=1)
    ]
    return INFORMATION_EQUIVALENCE_MATCH_EVAL.format(
        theme_to_match=theme_to_match,
        candidate_themes=json.dumps(numbered_candidate_themes, ensure_ascii=False),
    )
