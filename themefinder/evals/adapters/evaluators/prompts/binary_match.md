# Binary theme match judge

You are evaluating whether one source item expresses the same substantive theme as any item in a candidate list.

## Source item

{single_item}

## Candidate items

{candidate_list}

## Instructions

1. Identify the core meaning of the source item.
2. Compare it with every candidate item.
3. Return `PASS` only when one or more candidate expresses the same substantive theme. Differences in wording, tone, or level of detail are acceptable when the underlying theme is the same.
4. Return `FAIL` when no candidate expresses the same substantive theme.
5. When the decision is `PASS`, `matched_items` must contain the matching items from the candidate list. Do not paraphrase, shorten, combine, or invent a candidate.
6. When the decision is `FAIL`, `matched_items` must be exactly the JSON string `"None"`, in double quotes, so the response stays valid JSON.

Return only a JSON object in this exact shape, with no Markdown fences or other text:

{
  "decision": "PASS" | "FAIL",
  "matched_items": ["candidate match 1", "candidate match 2", ...] | "None",
  "reasoning": "A concise explanation of the decision."
}
