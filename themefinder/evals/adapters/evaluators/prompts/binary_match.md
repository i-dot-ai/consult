# Binary theme match judge

You are evaluating whether one source item expresses the same substantive theme as any item in a candidate list.

## Source item

{item}

## Candidate items

{candidates}

## Instructions

1. Identify the core meaning of the source item.
2. Compare it with every candidate item.
3. Return `PASS` only when one candidate expresses the same substantive theme. Differences in wording, tone, or level of detail are acceptable when the underlying theme is the same.
4. Return `FAIL` when no candidate expresses the same substantive theme.
5. When the decision is `PASS`, `matched_item` must reproduce exactly one item from the candidate list. Do not paraphrase, shorten, combine, or invent a candidate.
6. When the decision is `FAIL`, `matched_item` must be exactly `N/A`.

Return only a JSON object in this exact shape, with no Markdown fences or other text:

```json
{
  "decision": "PASS" | "FAIL",
  "matched_item": "exact candidate item" | "N/A",
  "reasoning": "A concise explanation of the decision."
}
```
