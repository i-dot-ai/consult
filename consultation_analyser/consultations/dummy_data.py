from consultation_analyser.hosting_environment import HostingEnvironment
from tests.factories import (
    FakeConsultationData,
    QuestionFactory,
    ConsultationFactory,
    SectionFactory,
    AnswerFactory,
    ConsultationResponseFactory,
)


class DummyConsultation:
    def __init__(self, responses=10, **options):
        if not HostingEnvironment.is_local():
            raise RuntimeError("Dummy data generation should only be run in development")

        consultation = ConsultationFactory(**options)
        section = SectionFactory(name="Base section", consultation=consultation)
        questions = [QuestionFactory(question=q, section=section) for q in FakeConsultationData().all_questions()]
        for r in range(responses):
            response = ConsultationResponseFactory()
            _answers = [AnswerFactory(question=q, consultation_response=response) for q in questions]
