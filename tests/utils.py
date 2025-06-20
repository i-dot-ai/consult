from consultation_analyser.consultations import models


def get_sorted_theme_string(themes: list[models.Theme]) -> str:
    return ", ".join(sorted([theme.key if theme.key else theme.name for theme in themes]))
