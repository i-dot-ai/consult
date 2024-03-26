"""
For now, dummy code to test consultation flow.
"""

import datetime
import random

from . import models


def dummy_generate_theme_for_question(question):
    # This generates junk themes for us to test things
    answers_qs = models.Answer.objects.filter(question=question)
    made_up_themes = []
    for i in range(3):
        label = f"Theme {i}: {question.slug} : {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}"
        words = question.text.split()
        keywords = [random.choice(words), random.choice(words)]
        theme = models.Theme(keywords=keywords, label=label)
        theme.save()
        made_up_themes.append(theme)
    for answer in answers_qs:
        answer.theme = random.choice(made_up_themes)
        answer.save()


def dummy_save_themes_for_consultation(consultation_slug: str) -> None:
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug, has_free_text=True)
    for question in questions:
        dummy_generate_theme_for_question(question)
