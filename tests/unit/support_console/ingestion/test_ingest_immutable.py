"""
Tests for immutable data ingestion workflow.
"""

import pytest

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations.models import (
    Consultation,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
)
from consultation_analyser.ingest.ingestion.ingest_immutable import (
    _ingest_questions,
    _ingest_respondents,
    _ingest_responses,
    ingest_immutable_data,
)
from consultation_analyser.ingest.ingestion.pydantic_models import (
    ImmutableDataBatch,
    MultiChoiceInput,
    QuestionInput,
    RespondentInput,
    ResponseInput,
)


@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create(email="test@example.com")


@pytest.fixture
def consultation(db):
    """Create a test consultation"""
    return Consultation.objects.create(code="TEST", title="Test Consultation")


class TestIngestRespondents:
    """Tests for _ingest_respondents function"""

    def test_ingest_respondents_basic(self, db, consultation):
        """Test ingesting respondents without demographics"""
        respondents = [
            RespondentInput(themefinder_id=1, demographic_data={}),
            RespondentInput(themefinder_id=2, demographic_data={}),
        ]

        _ingest_respondents(consultation, respondents)

        # Verify respondents created
        assert Respondent.objects.filter(consultation=consultation).count() == 2
        r1 = Respondent.objects.get(consultation=consultation, themefinder_id=1)
        r2 = Respondent.objects.get(consultation=consultation, themefinder_id=2)
        assert r1.demographics.count() == 0
        assert r2.demographics.count() == 0

    def test_ingest_respondents_with_demographics(self, db, consultation):
        """Test ingesting respondents with demographics"""
        respondents = [
            RespondentInput(
                themefinder_id=1, demographic_data={"age": ["25-34"], "region": ["London"]}
            ),
            RespondentInput(themefinder_id=2, demographic_data={"age": ["35-44"]}),
        ]

        _ingest_respondents(consultation, respondents)

        # Verify respondents created
        assert Respondent.objects.filter(consultation=consultation).count() == 2

        r1 = Respondent.objects.get(consultation=consultation, themefinder_id=1)
        assert r1.demographics.count() == 2

        # Verify demographic options created
        age_option = DemographicOption.objects.get(
            consultation=consultation, field_name="age", field_value="25-34"
        )
        region_option = DemographicOption.objects.get(
            consultation=consultation, field_name="region", field_value="London"
        )
        assert age_option in r1.demographics.all()
        assert region_option in r1.demographics.all()

    def test_ingest_respondents_idempotent(self, db, consultation):
        """Test that re-running ingestion deletes existing respondents"""
        respondents = [RespondentInput(themefinder_id=1, demographic_data={})]

        # First run
        _ingest_respondents(consultation, respondents)
        assert Respondent.objects.filter(consultation=consultation).count() == 1

        # Second run with different data
        respondents = [
            RespondentInput(themefinder_id=2, demographic_data={}),
            RespondentInput(themefinder_id=3, demographic_data={}),
        ]
        _ingest_respondents(consultation, respondents)

        # Should have new respondents, not old ones
        assert Respondent.objects.filter(consultation=consultation).count() == 2
        assert not Respondent.objects.filter(consultation=consultation, themefinder_id=1).exists()


class TestIngestQuestions:
    """Tests for _ingest_questions function"""

    def test_ingest_questions_free_text_only(self, db, consultation):
        """Test ingesting free text questions"""
        questions = [
            QuestionInput(
                question_text="What do you think?", question_number=1, has_free_text=True
            ),
            QuestionInput(
                question_text="Any other comments?", question_number=2, has_free_text=True
            ),
        ]

        _ingest_questions(consultation, questions)

        # Verify questions created
        assert Question.objects.filter(consultation=consultation).count() == 2
        q1 = Question.objects.get(consultation=consultation, number=1)
        assert q1.text == "What do you think?"
        assert q1.has_free_text is True
        assert q1.has_multiple_choice is False

    def test_ingest_questions_with_multi_choice(self, db, consultation):
        """Test ingesting questions with multi-choice options"""
        questions = [
            QuestionInput(
                question_text="Choose options:",
                question_number=1,
                has_free_text=False,
                multi_choice_options=["Option A", "Option B", "Option C"],
            ),
        ]

        _ingest_questions(consultation, questions)

        # Verify question created
        q1 = Question.objects.get(consultation=consultation, number=1)
        assert q1.has_multiple_choice is True
        assert q1.has_free_text is False

        # Verify multi-choice options created
        options = MultiChoiceAnswer.objects.filter(question=q1)
        assert options.count() == 3
        assert set(options.values_list("text", flat=True)) == {
            "Option A",
            "Option B",
            "Option C",
        }

    def test_ingest_questions_idempotent(self, db, consultation):
        """Test that re-running ingestion deletes existing questions"""
        questions = [QuestionInput(question_text="Q1", question_number=1, has_free_text=True)]

        # First run
        _ingest_questions(consultation, questions)
        assert Question.objects.filter(consultation=consultation).count() == 1

        # Second run with different questions
        questions = [
            QuestionInput(question_text="Q2", question_number=2, has_free_text=True),
            QuestionInput(question_text="Q3", question_number=3, has_free_text=True),
        ]
        _ingest_questions(consultation, questions)

        # Should have new questions, not old ones
        assert Question.objects.filter(consultation=consultation).count() == 2
        assert not Question.objects.filter(consultation=consultation, number=1).exists()


class TestIngestResponses:
    """Tests for _ingest_responses function"""

    def test_ingest_responses_free_text(self, db, consultation):
        """Test ingesting free text responses"""
        # Setup
        respondent1 = Respondent.objects.create(consultation=consultation, themefinder_id=1)
        respondent2 = Respondent.objects.create(consultation=consultation, themefinder_id=2)
        question = Question.objects.create(
            consultation=consultation, text="What do you think?", number=1, has_free_text=True
        )

        responses_by_question = {
            1: [
                ResponseInput(themefinder_id=1, text="I think it's great"),
                ResponseInput(themefinder_id=2, text="I have concerns"),
            ]
        }

        _ingest_responses(consultation, responses_by_question, {})

        # Verify responses created
        assert Response.objects.filter(question=question).count() == 2

        r1 = Response.objects.get(question=question, respondent=respondent1)
        assert r1.free_text == "I think it's great"

        r2 = Response.objects.get(question=question, respondent=respondent2)
        assert r2.free_text == "I have concerns"

        # Verify question total_responses updated
        question.refresh_from_db()
        assert question.total_responses == 2

    def test_ingest_responses_multi_choice(self, db, consultation):
        """Test ingesting multi-choice responses"""
        # Setup
        respondent1 = Respondent.objects.create(consultation=consultation, themefinder_id=1)
        question = Question.objects.create(
            consultation=consultation,
            text="Choose options:",
            number=1,
            has_free_text=False,
            has_multiple_choice=True,
        )
        option_a = MultiChoiceAnswer.objects.create(question=question, text="Option A")
        option_b = MultiChoiceAnswer.objects.create(question=question, text="Option B")

        multi_choice_by_question = {
            1: [MultiChoiceInput(themefinder_id=1, options=["Option A", "Option B"])]
        }

        _ingest_responses(consultation, {}, multi_choice_by_question)

        # Verify response created with multi-choice selections
        response = Response.objects.get(question=question, respondent=respondent1)
        assert response.chosen_options.count() == 2
        assert option_a in response.chosen_options.all()
        assert option_b in response.chosen_options.all()

    def test_ingest_responses_mixed(self, db, consultation):
        """Test ingesting both free text and multi-choice for same respondent"""
        # Setup
        respondent1 = Respondent.objects.create(consultation=consultation, themefinder_id=1)
        question = Question.objects.create(
            consultation=consultation,
            text="Question with both:",
            number=1,
            has_free_text=True,
            has_multiple_choice=True,
        )
        option_a = MultiChoiceAnswer.objects.create(question=question, text="Option A")

        responses_by_question = {1: [ResponseInput(themefinder_id=1, text="My comment")]}
        multi_choice_by_question = {1: [MultiChoiceInput(themefinder_id=1, options=["Option A"])]}

        _ingest_responses(consultation, responses_by_question, multi_choice_by_question)

        # Verify single response with both free text and multi-choice
        assert Response.objects.filter(question=question).count() == 1
        response = Response.objects.get(question=question, respondent=respondent1)
        assert response.free_text == "My comment"
        assert response.chosen_options.count() == 1
        assert option_a in response.chosen_options.all()

    def test_ingest_responses_missing_respondent(self, db, consultation):
        """Test that responses with unknown respondent are skipped"""
        question = Question.objects.create(
            consultation=consultation, text="Test", number=1, has_free_text=True
        )

        responses_by_question = {
            1: [ResponseInput(themefinder_id=999, text="From unknown respondent")]
        }

        _ingest_responses(consultation, responses_by_question, {})

        # Should not create response for unknown respondent
        assert Response.objects.filter(question=question).count() == 0


class TestIngestImmutableData:
    """Tests for full ingest_immutable_data function"""

    def test_ingest_complete_batch(self, db, user):
        """Test ingesting a complete immutable data batch"""
        batch = ImmutableDataBatch(
            consultation_code="NHS_2024",
            consultation_title="NHS Consultation 2024",
            respondents=[
                RespondentInput(themefinder_id=1, demographic_data={"age": ["25-34"]}),
                RespondentInput(themefinder_id=2, demographic_data={"age": ["35-44"]}),
            ],
            questions=[
                QuestionInput(
                    question_text="What do you think?", question_number=1, has_free_text=True
                ),
                QuestionInput(
                    question_text="Choose options:",
                    question_number=2,
                    has_free_text=False,
                    multi_choice_options=["Option A", "Option B"],
                ),
            ],
            responses_by_question={
                1: [
                    ResponseInput(themefinder_id=1, text="Great idea"),
                    ResponseInput(themefinder_id=2, text="Not sure"),
                ]
            },
            multi_choice_by_question={
                2: [MultiChoiceInput(themefinder_id=1, options=["Option A"])]
            },
        )

        consultation_id = ingest_immutable_data(batch, user.id)

        # Verify consultation created
        consultation = Consultation.objects.get(id=consultation_id)
        assert consultation.code == "NHS_2024"
        assert consultation.title == "NHS Consultation 2024"
        assert user in consultation.users.all()

        # Verify respondents created
        assert Respondent.objects.filter(consultation=consultation).count() == 2

        # Verify questions created
        assert Question.objects.filter(consultation=consultation).count() == 2
        q1 = Question.objects.get(consultation=consultation, number=1)
        q2 = Question.objects.get(consultation=consultation, number=2)

        # Verify responses created for question 1
        assert Response.objects.filter(question=q1).count() == 2

        # Verify multi-choice response for question 2
        assert Response.objects.filter(question=q2).count() == 1
        response = Response.objects.get(question=q2)
        assert response.chosen_options.count() == 1

    def test_ingest_idempotent(self, db, user):
        """Test that re-running ingestion updates rather than duplicates"""
        batch = ImmutableDataBatch(
            consultation_code="TEST",
            consultation_title="Test V1",
            respondents=[RespondentInput(themefinder_id=1)],
            questions=[QuestionInput(question_text="Q1", question_number=1)],
        )

        # First run
        consultation_id_1 = ingest_immutable_data(batch, user.id)

        # Second run with updated title
        batch.consultation_title = "Test V2"
        consultation_id_2 = ingest_immutable_data(batch, user.id)

        # Should be same consultation
        assert consultation_id_1 == consultation_id_2

        consultation = Consultation.objects.get(id=consultation_id_1)
        assert consultation.title == "Test V2"

        # Should not duplicate respondents or questions
        assert Respondent.objects.filter(consultation=consultation).count() == 1
        assert Question.objects.filter(consultation=consultation).count() == 1
        assert Consultation.objects.filter(code="TEST").count() == 1
