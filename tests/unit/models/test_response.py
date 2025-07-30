import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.django_db
class TestResponse:
    def test_response_creation(self):
        """Test basic response creation"""
        response = factories.ResponseFactory()
        assert isinstance(response, models.Response)
        assert response.free_text
        assert response.chosen_options.count() == 0
        assert response.respondent
        assert response.question

    def test_response_with_multiple_choice(self):
        """Test response with multiple choice selections"""
        response = factories.ResponseWithMultipleChoiceFactory()
        assert response.free_text == ""
        assert response.chosen_options.count() >= 1
        assert all(
            opt in response.question.multiple_choice_options
            for opt in response.chosen_options.all()
        )

    def test_response_with_both(self):
        """Test response with both free text and multiple choice"""
        response = factories.ResponseWithBothFactory()
        assert response.free_text
        assert response.chosen_options.count() >= 1

    def test_unique_constraint(self):
        """Test that only one response per respondent per question is allowed"""
        response = factories.ResponseFactory()

        # Try to create another response for same respondent and question
        with pytest.raises(Exception):  # Will raise IntegrityError
            models.Response.objects.create(
                respondent=response.respondent,
                question=response.question,
                free_text="Duplicate response",
            )

    def test_response_annotation_relationship(self):
        """Test one-to-one relationship with ResponseAnnotation"""
        response = factories.ResponseFactory()
        annotation = factories.ResponseAnnotationFactory(response=response)

        assert response.annotation == annotation
        assert annotation.response == response
