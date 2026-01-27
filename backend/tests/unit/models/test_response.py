import pytest
from backend import factories
from backend.consultations import models
from backend.consultations.models import Response
from django.contrib.postgres.search import SearchQuery


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
                question=response.free_text_question,
                free_text="Duplicate response",
            )

    def test_response_annotation_relationship(self):
        """Test one-to-one relationship with ResponseAnnotation"""
        response = factories.ResponseFactory()
        annotation = factories.ResponseAnnotationFactory(response=response)

        assert response.annotation == annotation
        assert annotation.response == response


@pytest.mark.django_db
@pytest.mark.parametrize("text", ["support workers", "support worker", "supported worker"])
def test_indexing(text):
    response = factories.ResponseFactory(free_text=text)
    response.save()
    response.refresh_from_db()
    # we expect all texts to have the same representation
    assert response.search_vector == "'support':1 'worker':2"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "search_text", ["the support workers", "a support worker", "supported worker"]
)
def test_full_text_search(search_text):
    for text in "support workers", "support worker", "supported worker":
        response = factories.ResponseFactory(free_text=text)
        response.save()
        response.refresh_from_db()

    search_query = SearchQuery(search_text, config="english")
    # we expect all results to be returned
    assert Response.objects.filter(search_vector=search_query).count() == 3
