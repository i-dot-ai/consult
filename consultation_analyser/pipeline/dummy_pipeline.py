from uuid import UUID

from faker import Faker

from consultation_analyser.consultations import models


def save_themes_for_consultation(consultation_id: UUID) -> None:
    faker = Faker()

    answers = (
        models.Answer.objects.select_related("question")
        .filter(question__section__consultation__id=consultation_id, question__has_free_text=True)
        .all()
    )

    topic_id = -1
    for answer in answers.all():
        random_themes = faker.words()
        for theme in random_themes:
            answer.save_theme_to_answer(theme, topic_id)
            topic_id += 1
