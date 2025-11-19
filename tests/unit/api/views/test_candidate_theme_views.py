import pytest
from django.urls import reverse

from consultation_analyser.consultations.models import SelectedTheme
from consultation_analyser.factories import CandidateThemeFactory
from tests.utils import isoformat


@pytest.mark.django_db
class TestCandidateThemeViewSet:
    def test_get_candidate_themes(
        self, client, consultation_user_token, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint returns candidate themes for a question with nested children"""
        # Build a candidate theme tree:
        # root1
        #   ├─ child1 (selected)
        #   │   └─ grandchild1
        #   └─ child2
        # root2 (selected)

        root1 = CandidateThemeFactory(
            question=free_text_question, parent=None, approximate_frequency=35
        )
        child1 = CandidateThemeFactory(
            question=free_text_question, parent=root1, selectedtheme=theme_a
        )
        grandchild1 = CandidateThemeFactory(question=free_text_question, parent=child1)
        child2 = CandidateThemeFactory(question=free_text_question, parent=root1)
        root2 = CandidateThemeFactory(
            question=free_text_question,
            parent=None,
            selectedtheme=theme_b,
            approximate_frequency=60,  # higher frequency than root1
        )

        url = reverse(
            "candidate-theme-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data == {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                # Listed in descending order of parent approximate_frequency
                {
                    "id": str(root2.id),
                    "name": root2.name,
                    "description": root2.description,
                    "selectedtheme_id": str(theme_b.id),
                    "children": [],
                },
                {
                    "id": str(root1.id),
                    "name": root1.name,
                    "description": root1.description,
                    "selectedtheme_id": None,
                    "children": [
                        {
                            "id": str(child1.id),
                            "name": child1.name,
                            "description": child1.description,
                            "selectedtheme_id": str(theme_a.id),
                            "children": [
                                {
                                    "id": str(grandchild1.id),
                                    "name": grandchild1.name,
                                    "description": grandchild1.description,
                                    "selectedtheme_id": None,
                                    "children": [],
                                }
                            ],
                        },
                        {
                            "id": str(child2.id),
                            "name": child2.name,
                            "description": child2.description,
                            "selectedtheme_id": None,
                            "children": [],
                        },
                    ],
                },
            ],
        }

    def test_select_candidate_theme(
        self,
        client,
        consultation_user,
        consultation_user_token,
        free_text_question,
        candidate_theme,
    ):
        """Test API endpoint to select a candidate theme and create a SelectedTheme"""
        url = reverse(
            "candidate-theme-select",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": candidate_theme.id,
            },
        )
        response = client.post(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        candidate_theme.refresh_from_db()
        selected_theme = SelectedTheme.objects.get(pk=candidate_theme.selectedtheme_id)

        assert selected_theme.id == candidate_theme.selectedtheme_id
        assert selected_theme.name == candidate_theme.name
        assert selected_theme.description == candidate_theme.description
        assert selected_theme.question == free_text_question
        assert selected_theme.version == 1
        assert selected_theme.last_modified_by == consultation_user

        assert response.status_code == 201
        assert response.json() == {
            "id": str(selected_theme.id),
            "name": selected_theme.name,
            "description": selected_theme.description,
            "version": selected_theme.version,
            "modified_at": isoformat(selected_theme.modified_at),
            "last_modified_by": consultation_user.email,
        }

        # now we post the same theme again and we expect to get an error
        response = client.post(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 400
        assert response.json() == {
            "detail": "this theme has already been selected",
        }
