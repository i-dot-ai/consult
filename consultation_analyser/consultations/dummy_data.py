import datetime
import random

from consultation_analyser.factories import (
    AnswerFactory,
    ConsultationFactory,
    ConsultationResponseFactory,
    FakeConsultationData,
    QuestionFactory,
    SectionFactory,
    ThemeFactory,
)
from consultation_analyser.hosting_environment import HostingEnvironment


def create_dummy_data(responses=10, include_themes=True, number_questions=10, **options):
    if number_questions > 10:
        raise RuntimeError("You can't have more than 10 questions")
    if HostingEnvironment.is_production():
        raise RuntimeError("Dummy data generation should not be run in production")

    # Timestamp to avoid duplicates - set these as default options
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    if "name" not in options:
        options["name"] = f"Dummy consultation generated at {timestamp}"
    if "slug" not in options:
        options["slug"] = f"consultation-slug-{timestamp}"

    consultation = ConsultationFactory(**options)
    section = SectionFactory(name="Base section", consultation=consultation)
    fake_consultation_data = FakeConsultationData()
    all_questions = fake_consultation_data.all_questions()
    questions_to_include = all_questions[:number_questions]

    questions = [
        QuestionFactory(
            text=q["text"],
            slug=q["slug"],
            multiple_choice_questions=[
                (x["question_text"], x["options"]) for x in (q.get("multiple_choice") or [])
            ],
            has_free_text=q["has_free_text"],
            section=section,
        )
        for q in questions_to_include
    ]
    for r in range(responses):
        response = ConsultationResponseFactory(consultation=consultation)
        answers = []
        for q in questions:
            if q.has_free_text:
                free_text_answer = fake_consultation_data.get_free_text_answer(q.slug)
                answers.append(
                    AnswerFactory(
                        question=q,
                        consultation_response=response,
                        free_text=free_text_answer,
                        theme=None,
                    )
                )
                # Force some answers to have no free text response
                if random.randrange(1, 4) == 1:
                    answers.append(
                        AnswerFactory(
                            question=q,
                            consultation_response=response,
                            free_text="",
                            theme=None,
                        )
                    )
            else:
                answers.append(
                    AnswerFactory(question=q, consultation_response=response, theme=None)
                )
        if include_themes:
            # Set themes per question, multiple answers with the same theme
            for q in questions:
                themes = [ThemeFactory(topic_id=i) for i in range(-1, 4)]
                for a in answers:
                    random_theme = random.choice(themes)
                    a.theme = random_theme
                    a.save()
            # Force at least one answer to be an outlier
            a = random.choice(answers)
            a.theme = themes[0]
            a.save()
    return consultation
