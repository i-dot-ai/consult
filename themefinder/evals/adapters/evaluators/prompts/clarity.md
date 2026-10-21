You are evaluating whether one refined theme is simple and clear.

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

{
  "decision": "PASS" | "FAIL",
  "reasoning": "A brief explanation of the decision."
}
