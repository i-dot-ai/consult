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


class DummyConsultation:
    def __init__(self, responses=10, include_themes=True, **options):
        if not HostingEnvironment.is_development_environment():
            raise RuntimeError("Dummy data generation should only be run in development")

        # Timestamp to avoid duplicates - set these as default options
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        if "name" not in options:
            options["name"] = f"Dummy consultation generated at {timestamp}"
        if "slug" not in options:
            options["slug"] = f"consultation-slug-{timestamp}"

        consultation = ConsultationFactory(**options)
        section = SectionFactory(name="Base section", consultation=consultation)
        questions = [
            QuestionFactory(
                text=q["text"],
                slug=q["slug"],
                multiple_choice_options=q.get("multiple_choice_options", None),
                has_free_text=q["has_free_text"],
                section=section,
            )
            for q in FakeConsultationData().all_questions()
        ]
        for r in range(responses):
            response = ConsultationResponseFactory(consultation=consultation)
            if include_themes:
                _answers = [AnswerFactory(question=q, consultation_response=response) for q in questions]

                # Set themes per question, multiple answers with the same theme
                for q in questions:
                    themes = [ThemeFactory() for _ in range(2, 6)]
                    themes.append(ThemeFactory(is_outlier=True))  # include an outlier
                    for a in _answers:
                        random_theme = random.choice(themes)
                        a.theme = random_theme
                        a.save()
                # Force at least one answer to be an outlier
                a = random.choice(_answers)
                a.theme = themes[-1]

            else:
                _answers = [AnswerFactory(question=q, consultation_response=response, theme=None) for q in questions]
