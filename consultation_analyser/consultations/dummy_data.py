import datetime
import random

from consultation_analyser.factories import (
    ConsultationBuilder,
    FakeConsultationData,
)
from consultation_analyser.hosting_environment import HostingEnvironment


def create_dummy_data(responses=20, number_questions=10, **options):
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

    consultation_builder = ConsultationBuilder(**options)
    fake_consultation_data = FakeConsultationData()
    all_questions = fake_consultation_data.all_questions()
    questions_to_include = all_questions[:number_questions]

    questions = [
        consultation_builder.add_question(
            text=q["text"],
            slug=q["slug"],
            multiple_choice_questions=[
                (x["question_text"], x["options"]) for x in (q.get("multiple_choice") or [])
            ],
            has_free_text=q["has_free_text"],
        )
        for q in questions_to_include
    ]

    for i, r in enumerate(range(responses)):
        for q in questions:
            if q.has_free_text:
                if random.randrange(1, 4) == 1:
                    free_text_answer = ""
                else:
                    free_text_answer = fake_consultation_data.get_free_text_answer(q.slug)
            else:
                free_text_answer = None

            consultation_builder.add_answer(q, free_text=free_text_answer)
            consultation_builder.next_response()

    # always assign a double multichoice selection to the last question
    question_options = q.multiple_choice_options[0]
    answers = (question_options["question_text"], question_options["options"][:2])
    consultation_builder.add_answer(q, multiple_choice_answers=[answers])

    return consultation_builder.consultation
