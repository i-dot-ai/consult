"""
Use LLMs to generate summaries for themes. More to follow!
"""

from consultation_analyser.consultations.models import Theme


def dummy_generate_theme_summary(theme: Theme) -> str:
    made_up_summary = (theme.keywords).join(", ")
    return made_up_summary
