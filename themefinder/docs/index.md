# Welcome to ThemeFinder

ThemeFinder is a topic modelling Python package designed for analyzing one-to-many question-answer data (i.e. survey responses, public consultations, etc.).


## Quickstart
See [README](https://github.com/i-dot-ai/themefinder) for how to get started with this package.


## ThemeFinder pipeline

ThemeFinder's pipeline consists of five distinct stages, each utilizing a specialized LLM prompt:

### Sentiment analysis
- Analyses the emotional tone and position of each response using sentiment-focused prompts
- Provides structured sentiment categorisation based on LLM analysis

### Theme generation
- Uses exploratory prompts to identify initial themes from response batches
- Groups related responses for better context through guided theme extraction

### Theme condensation
- Employs comparative prompts to combine similar or overlapping themes
- Reduces redundancy in identified topics through systematic theme evaluation

### Theme refinement
- Leverages standardisation prompts to normalise theme descriptions
- Creates clear, consistent theme definitions through structured refinement

### Theme target alignment
- Optional step to consolidate themes down to a target number

### Theme mapping
- Utilizes classification prompts to map individual responses to refined themes
- Supports multiple theme assignments per response through detailed analysis


The prompts used at each stage can be found in `src/themefinder/prompts/`.

The file `src/themefinder.core.py` contains the function `find_themes` which runs the pipeline. It also contains functions for each individual stage.