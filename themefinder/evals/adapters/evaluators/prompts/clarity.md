You are evaluating whether one refined theme is simple and clear.

Assess only the wording of the theme label and description.

- **PASS**: Together, the label and description communicate the theme's meaning in simple, clear language that is easy to understand.
- **FAIL**: The wording is confusing, unnecessarily complex, ambiguous, or otherwise difficult to understand.

Do not assess information equivalence, response references, distinctiveness, length, or whether this theme is better than any other theme. Do not infer meaning from original themes, source responses, or other refined themes.

## Output Format

Return strict JSON in this format. `decision` must be exactly `PASS` or `FAIL`.
{
    "decision": "PASS",
    "reasoning": "Brief explanation"
}

THEME LABEL:
{topic_label}

THEME DESCRIPTION:
{topic_description}
