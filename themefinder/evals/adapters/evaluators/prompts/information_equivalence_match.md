# Information equivalence theme match judge

You are evaluating whether one source theme expresses exactly the same
substantive information as one or more themes in a candidate list.

## Source theme

{single_item}

## Candidate themes

{candidate_list}

## Instructions

1. Compare the source theme with every candidate theme.
2. A candidate matches only when it preserves all material information in the
   source theme, including its subject, claim, scope, qualifiers, and sentiment
   or position. Different wording is acceptable.
3. Do not match themes that are merely related, broader, narrower,
   contradictory, or that add or omit material information.
4. Return `PASS` when one or more candidates match. `matched_items` must list
   every matching candidate exactly as it appears in the candidate list.
5. Return `FAIL` when no candidate matches. `matched_items` must then be
   exactly `None`.

Return only a JSON object in this exact shape, with no Markdown fences or other
text:

{
  "decision": "PASS" | "FAIL",
  "matched_items": ["candidate match 1", "candidate match 2", ...] | "None",
  "reasoning": "A concise explanation of the decision."
}
