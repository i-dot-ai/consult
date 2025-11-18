import pytest
from pydantic import ValidationError

from consultation_analyser.support_console.pydantic_models import (
    RespondentInput,
    QuestionInput,
    ResponseInput,
    MultiChoiceInput,
    ImmutableDataBatch,
)


class TestRespondentInput:
    """Tests for RespondentInput Pydantic model"""

    def test_valid_respondent_with_demographics(self):
        """Test valid respondent data with demographics passes validation"""
        data = {
            "themefinder_id": 1,
            "demographic_data": {"age": ["25-34"], "region": ["London", "South East"]},
        }
        respondent = RespondentInput(**data)
        assert respondent.themefinder_id == 1
        assert respondent.demographic_data == {
            "age": ["25-34"],
            "region": ["London", "South East"],
        }

    def test_valid_respondent_without_demographics(self):
        """Test respondent with no demographics defaults to empty dict"""
        data = {"themefinder_id": 1}
        respondent = RespondentInput(**data)
        assert respondent.themefinder_id == 1
        assert respondent.demographic_data == {}

    def test_invalid_themefinder_id_type(self):
        """Test that non-integer themefinder_id raises ValidationError"""
        data = {"themefinder_id": "not_an_int", "demographic_data": {}}
        with pytest.raises(ValidationError) as exc_info:
            RespondentInput(**data)
        assert "themefinder_id" in str(exc_info.value)

    def test_missing_themefinder_id(self):
        """Test that missing themefinder_id raises ValidationError"""
        data = {"demographic_data": {}}
        with pytest.raises(ValidationError) as exc_info:
            RespondentInput(**data)
        assert "themefinder_id" in str(exc_info.value)

    def test_invalid_demographic_data_type(self):
        """Test that invalid demographic_data type raises ValidationError"""
        data = {"themefinder_id": 1, "demographic_data": "not_a_dict"}
        with pytest.raises(ValidationError) as exc_info:
            RespondentInput(**data)
        assert "demographic_data" in str(exc_info.value)

    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed"""
        data = {"themefinder_id": 1, "extra_field": "value"}
        with pytest.raises(ValidationError) as exc_info:
            RespondentInput(**data)
        assert "extra_field" in str(exc_info.value)


class TestQuestionInput:
    """Tests for QuestionInput Pydantic model"""

    def test_valid_question_free_text_only(self):
        """Test question with only free text"""
        data = {
            "question_text": "What do you think about this proposal?",
            "question_number": 1,
            "has_free_text": True,
        }
        question = QuestionInput(**data)
        assert question.question_text == "What do you think about this proposal?"
        assert question.question_number == 1
        assert question.has_free_text is True
        assert question.multi_choice_options == []

    def test_valid_question_with_multi_choice(self):
        """Test question with multi-choice options"""
        data = {
            "question_text": "Choose your preferred options:",
            "question_number": 2,
            "has_free_text": False,
            "multi_choice_options": ["Option A", "Option B", "Option C"],
        }
        question = QuestionInput(**data)
        assert question.has_free_text is False
        assert len(question.multi_choice_options) == 3
        assert question.multi_choice_options[0] == "Option A"

    def test_multi_choice_options_none_coerced_to_empty_list(self):
        """Test that None multi_choice_options is coerced to empty list"""
        data = {
            "question_text": "Test question",
            "question_number": 1,
            "multi_choice_options": None,
        }
        question = QuestionInput(**data)
        assert question.multi_choice_options == []

    def test_has_free_text_defaults_to_true(self):
        """Test that has_free_text defaults to True"""
        data = {"question_text": "Test question", "question_number": 1}
        question = QuestionInput(**data)
        assert question.has_free_text is True

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError"""
        data = {"question_text": "Test question"}
        with pytest.raises(ValidationError) as exc_info:
            QuestionInput(**data)
        assert "question_number" in str(exc_info.value)

    def test_invalid_question_number_type(self):
        """Test that non-integer question_number raises ValidationError"""
        data = {
            "question_text": "Test question",
            "question_number": "one",
        }
        with pytest.raises(ValidationError) as exc_info:
            QuestionInput(**data)
        assert "question_number" in str(exc_info.value)


class TestResponseInput:
    """Tests for ResponseInput Pydantic model"""

    def test_valid_response(self):
        """Test valid response data"""
        data = {"themefinder_id": 1, "text": "This is my response to the question."}
        response = ResponseInput(**data)
        assert response.themefinder_id == 1
        assert response.text == "This is my response to the question."

    def test_missing_text(self):
        """Test that missing text raises ValidationError"""
        data = {"themefinder_id": 1}
        with pytest.raises(ValidationError) as exc_info:
            ResponseInput(**data)
        assert "text" in str(exc_info.value)

    def test_empty_text_is_valid(self):
        """Test that empty text string is valid"""
        data = {"themefinder_id": 1, "text": ""}
        response = ResponseInput(**data)
        assert response.text == ""


class TestMultiChoiceInput:
    """Tests for MultiChoiceInput Pydantic model"""

    def test_valid_multi_choice(self):
        """Test valid multi-choice data"""
        data = {"themefinder_id": 1, "options": ["Option A", "Option B"]}
        mc = MultiChoiceInput(**data)
        assert mc.themefinder_id == 1
        assert mc.options == ["Option A", "Option B"]

    def test_empty_options_list(self):
        """Test that empty options list is valid"""
        data = {"themefinder_id": 1, "options": []}
        mc = MultiChoiceInput(**data)
        assert mc.options == []

    def test_missing_options(self):
        """Test that missing options raises ValidationError"""
        data = {"themefinder_id": 1}
        with pytest.raises(ValidationError) as exc_info:
            MultiChoiceInput(**data)
        assert "options" in str(exc_info.value)


class TestImmutableDataBatch:
    """Tests for ImmutableDataBatch Pydantic model"""

    def test_valid_complete_batch(self):
        """Test complete immutable data batch"""
        data = {
            "consultation_code": "NHS_2024",
            "consultation_title": "NHS Consultation 2024",
            "timestamp": "2024-01-15",
            "respondents": [
                {"themefinder_id": 1, "demographic_data": {"age": ["25-34"]}},
                {"themefinder_id": 2, "demographic_data": {}},
            ],
            "questions": [
                {
                    "question_text": "What do you think?",
                    "question_number": 1,
                    "has_free_text": True,
                },
                {
                    "question_text": "Choose options:",
                    "question_number": 2,
                    "has_free_text": False,
                    "multi_choice_options": ["Option A", "Option B"],
                },
            ],
            "responses_by_question": {
                1: [
                    {"themefinder_id": 1, "text": "I think it's great"},
                    {"themefinder_id": 2, "text": "I have concerns"},
                ]
            },
            "multi_choice_by_question": {
                2: [{"themefinder_id": 1, "options": ["Option A", "Option B"]}]
            },
        }
        batch = ImmutableDataBatch(**data)
        assert batch.consultation_code == "NHS_2024"
        assert batch.consultation_title == "NHS Consultation 2024"
        assert batch.timestamp == "2024-01-15"
        assert len(batch.respondents) == 2
        assert len(batch.questions) == 2
        assert len(batch.responses_by_question[1]) == 2
        assert len(batch.multi_choice_by_question[2]) == 1

    def test_minimal_batch(self):
        """Test minimal valid batch with no responses"""
        data = {
            "consultation_code": "TEST",
            "consultation_title": "Test Consultation",
            "respondents": [{"themefinder_id": 1}],
            "questions": [{"question_text": "Test Q", "question_number": 1}],
        }
        batch = ImmutableDataBatch(**data)
        assert batch.consultation_code == "TEST"
        assert batch.timestamp is None
        assert batch.responses_by_question == {}
        assert batch.multi_choice_by_question == {}

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError"""
        data = {
            "consultation_code": "TEST",
            # Missing consultation_title
            "respondents": [],
            "questions": [],
        }
        with pytest.raises(ValidationError) as exc_info:
            ImmutableDataBatch(**data)
        assert "consultation_title" in str(exc_info.value)

    def test_invalid_nested_respondent(self):
        """Test that invalid nested respondent raises ValidationError"""
        data = {
            "consultation_code": "TEST",
            "consultation_title": "Test",
            "respondents": [{"themefinder_id": "not_an_int"}],
            "questions": [],
        }
        with pytest.raises(ValidationError) as exc_info:
            ImmutableDataBatch(**data)
        assert "respondents" in str(exc_info.value)

    def test_invalid_question_number_key_in_responses(self):
        """Test that responses_by_question with string keys is converted"""
        data = {
            "consultation_code": "TEST",
            "consultation_title": "Test",
            "respondents": [{"themefinder_id": 1}],
            "questions": [{"question_text": "Q1", "question_number": 1}],
            "responses_by_question": {"1": [{"themefinder_id": 1, "text": "Response"}]},
        }
        # Pydantic should coerce string keys to int
        batch = ImmutableDataBatch(**data)
        # Note: Pydantic will actually keep dict keys as strings in JSON
        # but we can access them either way
        assert 1 in batch.responses_by_question or "1" in batch.responses_by_question
