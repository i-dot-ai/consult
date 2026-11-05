# Gambling 1000 Dataset

**This dataset contains synthetic data for evaluation purposes only. It must not be interpreted as real consultation evidence.**

## Overview

- **Topic:** Gambling advertising during televised sport
- **Questions:** Two question parts: a potential advertising ban, and alternatives for responsible-gambling awareness
- **Size:** 1,000 synthetic respondents and 1,000 responses per question part (2,000 response records)
- **Intended use:** Comparing models and informing model-switch decisions at a higher response volume

## Generation and review

- **Generated:** 2026-11-05
- **Seed:** 42
- **Models:** `gpt-5-mini-sweden` for the reviewed theme design; `gpt-5-nano-sweden` for response generation
- **Theme design:** Reuses the reviewed Gambling XS question set and its 11 regular themes per question, plus `XX` (off-topic) and `XY` (low-quality) fallback themes.

Questions, themes, and response previews were reviewed before the full run. The response prompts do not expose internal theme identifiers, labels, or stance metadata; sampled responses were on-topic, varied, and free of those internal headings.

## Structure

`inputs/` contains the questions, respondents, and generated responses. `outputs/mapping/2026-11-05/` contains the corresponding themes, expected sentiment, mappings, and detail-detection records.
