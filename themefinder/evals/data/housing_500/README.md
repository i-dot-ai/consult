# Housing 500 Dataset

**This dataset contains synthetic data for evaluation purposes only. It must not be interpreted as real consultation evidence.**

## Overview

- **Topic:** Affordable housing supply and private renting
- **Questions:** Increasing the supply of affordable, good-quality homes; and improving security, affordability, and standards for private renters
- **Size:** 500 synthetic respondents and 500 responses per question part (1,000 response records)
- **Intended use:** Comparing models and informing model-switch decisions at a medium response volume

## Generation and review

- **Generated:** 2026-11-05
- **Seed:** 42
- **Models:** `gpt-5-mini-sweden` for reviewed theme design; `gpt-5-nano-sweden` for response generation
- **Theme design:** 14 regular themes for housing supply and 13 for private renting, with `XX` (off-topic) and `XY` (low-quality) fallback themes for each question.

Questions, themes, and response previews were reviewed before the full run. The responses were on-topic and varied, and did not include internal theme identifiers, labels, or stance metadata.

## Structure

`inputs/` contains the questions, respondents, and generated responses. `outputs/mapping/2026-11-05/` contains the corresponding themes, expected sentiment, mappings, and detail-detection records.
