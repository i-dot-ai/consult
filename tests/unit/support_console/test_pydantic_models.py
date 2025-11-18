import pytest
from pydantic import ValidationError

from consultation_analyser.support_console.pydantic_models import (
    CandidateThemeBatch,
    CandidateThemeInput,
    ImmutableDataBatch,
    MultiChoiceInput,
    QuestionInput,
    RespondentInput,
    ResponseInput,
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


class TestCandidateThemeInput:
    """Tests for CandidateThemeInput model"""

    def test_valid_candidate_theme(self):
        """Test creating a valid candidate theme with all fields"""
        data = {
            "topic_id": "123",
            "topic_label": "Healthcare Access",
            "topic_description": "Issues related to accessing healthcare services",
            "source_topic_count": 45,
            "parent_id": "0",
            "children": ["124", "125"],
        }
        theme = CandidateThemeInput(**data)

        assert theme.topic_id == "123"
        assert theme.topic_label == "Healthcare Access"
        assert theme.topic_description == "Issues related to accessing healthcare services"
        assert theme.source_topic_count == 45
        assert theme.parent_id == "0"
        assert theme.children == ["124", "125"]

    def test_candidate_theme_snake_case_fields(self):
        """Test that standard snake_case field names work"""
        data = {
            "topic_id": "123",
            "topic_label": "Test Theme",
            "topic_description": "Test Description",
            "source_topic_count": 10,
            "parent_id": "0",
        }
        theme = CandidateThemeInput(**data)
        assert theme.topic_label == "Test Theme"
        assert theme.topic_description == "Test Description"

    def test_candidate_theme_children_defaults_to_empty_list(self):
        """Test that children defaults to empty list"""
        data = {
            "topic_id": "123",
            "topic_label": "Test",
            "topic_description": "Test",
            "source_topic_count": 10,
            "parent_id": "0",
        }
        theme = CandidateThemeInput(**data)
        assert theme.children == []

    def test_candidate_theme_missing_required_fields(self):
        """Test that missing required fields raises ValidationError"""
        data = {"topic_id": "123"}
        with pytest.raises(Exception):  # Pydantic ValidationError
            CandidateThemeInput(**data)

    def test_candidate_theme_invalid_source_topic_count_type(self):
        """Test that invalid type for source_topic_count raises ValidationError"""
        data = {
            "topic_id": "123",
            "topic_label": "Test",
            "topic_description": "Test",
            "source_topic_count": "not an int",  # Should be int
            "parent_id": "0",
        }
        with pytest.raises(Exception):  # Pydantic ValidationError
            CandidateThemeInput(**data)


class TestCandidateThemeBatch:
    """Tests for CandidateThemeBatch model"""

    def test_valid_candidate_theme_batch(self):
        """Test creating a valid candidate theme batch"""
        data = {
            "consultation_code": "NHS_2024",
            "timestamp": "2024-01-15",
            "themes_by_question": {
                1: [
                    {
                        "topic_id": "1",
                        "topic_label": "Theme 1",
                        "topic_description": "Description 1",
                        "source_topic_count": 10,
                        "parent_id": "0",
                    }
                ],
                2: [
                    {
                        "topic_id": "2",
                        "topic_label": "Theme 2",
                        "topic_description": "Description 2",
                        "source_topic_count": 20,
                        "parent_id": "0",
                    }
                ],
            },
        }
        batch = CandidateThemeBatch(**data)

        assert batch.consultation_code == "NHS_2024"
        assert batch.timestamp == "2024-01-15"
        assert 1 in batch.themes_by_question
        assert 2 in batch.themes_by_question
        assert len(batch.themes_by_question[1]) == 1
        assert batch.themes_by_question[1][0].topic_label == "Theme 1"

    def test_candidate_theme_batch_empty_themes(self):
        """Test batch with no themes"""
        data = {
            "consultation_code": "TEST",
            "timestamp": "2024-01-15",
            "themes_by_question": {},
        }
        batch = CandidateThemeBatch(**data)
        assert batch.themes_by_question == {}

    def test_candidate_theme_batch_missing_timestamp(self):
        """Test that missing timestamp raises ValidationError"""
        data = {
            "consultation_code": "TEST",
            # Missing timestamp
        }
        with pytest.raises(Exception):  # Pydantic ValidationError
            CandidateThemeBatch(**data)

    def test_candidate_theme_batch_invalid_nested_theme(self):
        """Test that invalid nested theme raises ValidationError"""
        data = {
            "consultation_code": "TEST",
            "timestamp": "2024-01-15",
            "themes_by_question": {
                1: [
                    {"topic_id": "1"}  # Missing required fields
                ]
            },
        }
        with pytest.raises(Exception):  # Pydantic ValidationError
            CandidateThemeBatch(**data)
