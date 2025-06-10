from consultation_analyser.consultations import models


def get_sorted_theme_string(themes: list[models.ThemeOld]) -> str:
    return ", ".join(sorted([theme.get_identifier() for theme in themes]))
