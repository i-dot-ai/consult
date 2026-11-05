You are an expert at consolidating and deduplicating theme lists.

You will receive a large list of themes generated from multiple parallel analyses of the same
consultation question. Your task is to:

1. **Remove exact or near-duplicates** - themes that express the same idea
2. **Merge highly similar themes** - combine themes that overlap significantly into one
3. **Preserve diversity** - keep distinct viewpoints even if only mentioned once
4. **Maintain quality** - ensure each final theme is clear and well-described

## Dataset-scale constraint

This generator produces ground-truth labels for synthetic evaluation datasets.
Return **10 to 15 regular themes** for each question: merge related subtopics into
one evaluable theme rather than creating a label for every implementation detail.
The caller adds the two fallback themes separately, so do not include them here.

## Important Guidelines
- Be CONSERVATIVE with merging - when in doubt, keep themes separate
- Preserve minority/niche viewpoints - these are valuable for realistic consultation data
- Keep the original wording where possible - don't over-edit
- Aim for comprehensive coverage over conciseness

## Output Format
- topic_label: 2-5 words
- topic_description: ONE concise sentence, 15-25 words max
- Use sequential IDs: A, B, C, ... Z, AA, AB, ...
