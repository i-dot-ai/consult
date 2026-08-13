# `setup_consultation.py` validation checks

Classification of every check that runs when `setup_consultation.py` validates a
consultation, split by scope: per-sheet (one Q.U. sheet, no Responses involved)
vs. cross-sheet (multiple sheets, or Q.U. ↔ Responses).

## Per-sheet checks

Run independently on each of `Demographic`, `Open questions`, `Hybrid questions`,
`Multiple Choice`.

1. **Required fields populated** — every cell named in `QU_SHEET_SPECS[...][2]`
   must be non-blank for each row (`validate_data`, lines 243–266).
2. **Column ID format** — every `column_name` / `open_column` / `closed_column`
   value must match `^[A-Z]{1,3}\s*$` (i.e. look like `A`, `BF`, `AAC`)
   (lines 269–282).
3. **Question number is an integer** — each `question_number` in each sheet must
   parse as `int`. 

## Cross-sheet checks

### Across Q.U. sheets only (no Responses involved)

4. **No duplicate column references** — same Excel column letter must not appear
   in more than one Q.U. row across all Q.U. sheets (lines 285–304).
5. **Globally unique `question_number`** — `question_number` values must be
   unique across all Q.U. sheets combined; raises `ValueError` if not, because
   the number is used as an output directory name (lines 583–596).

### Q.U. ↔ Responses

6. **Q.U. column count ≤ Responses column count** — total distinct columns
   referenced across Q.U. sheets must not exceed `n_cols - 1` of Responses
   (lines 307–310).
7. **Q.U. columns exist in Responses** — every column letter referenced in any
   Q.U. row must exist in the Responses headers map (lines 312–325).
8. **Closed columns look multichoice** — closed-side columns must have
   uniqueness ratio ≤ 0.2 in the Responses data; otherwise warn "looks like free
   text". Applies to `Multiple Choice.column_name` and `Hybrid.closed_column`
   (lines 345–366, 391–410).
9. **Open columns look free-text** — open-side columns must have uniqueness
   ratio ≥ 0.2; otherwise warn "should this be on Multiple Choice?". Applies to
   `Open.column_name` and `Hybrid.open_column` (lines 368–389, 411–423).
10. **Label string similarity** — `SequenceMatcher` ratio between Q.U.
    `question_text` and the corresponding Responses header must be ≥ 0.4
    (lines 437–445).
11. **Number consistency in labels** — integers extracted from Q.U.
    `question_text` and from the Responses header must match when both contain
    numbers (lines 446–449).

### Demographics ↔ Responses

12. **Demographic `column_id` exists in Responses** — each demographic column
    letter must be present in `responses_df.columns`; otherwise flagged as "not
    found in response data" (lines 209–214).

### Responses-side coverage

13. **No unreferenced Response columns** — every Response column (excluding
    `themefinder_id` and any "Response ID"-style header) must be referenced
    either by a Q.U. row or as a demographic; otherwise flagged with a hint to
    consider adding it as a demographic (lines 462–487).

## Summary counts

- **Per-sheet rules**: 3 (required fields, column-ID format, integer
  `question_number`)
- **Cross-sheet rules**: 10
  - 2 across Q.U. sheets (duplicate columns, unique question numbers)
  - 6 Q.U. ↔ Responses (count, existence, closed-uniqueness, open-uniqueness,
    label similarity, number consistency)
  - 1 Demographics ↔ Responses (column existence)
  - 1 Responses coverage (unreferenced columns)
