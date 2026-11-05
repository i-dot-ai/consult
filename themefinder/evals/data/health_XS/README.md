# Health XS Dataset

**This dataset contains synthetic data for evaluation purposes only. It must not be interpreted as real consultation evidence.**

## Overview

- **Topic:** NHS service access and workforce planning
- **Questions:** Timely access to GP, community-health, and mental-health services; and priorities for NHS recruitment, retention, and safe care
- **Size:** 100 synthetic respondents and 100 responses per question part (200 response records)
- **Intended use:** Comparing models and informing model-switch decisions at a small response volume

## Generation and review

- **Generated:** 2026-11-05
- **Seed:** 1
- **Models:** `gpt-5-mini-sweden` for reviewed theme design; `gpt-5-nano-sweden` for response generation
- **Theme design:** 12 regular themes for service access and 14 for workforce planning, with `XX` (off-topic) and `XY` (low-quality) fallback themes for each question.

Questions, themes, and response previews were reviewed before the full run. The responses were on-topic and varied, and did not include internal theme identifiers, labels, or stance metadata.

## Structure

`inputs/` contains the questions, respondents, and generated responses. `outputs/mapping/2026-11-05/` contains the corresponding themes, expected sentiment, mappings, and detail-detection records.
