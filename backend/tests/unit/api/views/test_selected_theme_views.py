import json
from uuid import uuid4

import pytest
from django.urls import reverse

from consultations.models import SelectedTheme
from tests.utils import isoformat


@pytest.mark.django_db
class TestSelectedThemeViewSet:
    def test_get_selected_themes(
        self, client, staff_user_token, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint returns selected themes for a question"""
        url = reverse(
            "selected-theme-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200

        data = response.json()
        assert data == {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": str(theme_a.id),
                    "name": "Theme A",
                    "description": theme_a.description,
                    "version": 2,
                    "modified_at": isoformat(theme_a.modified_at),
                    "last_modified_by": theme_a.last_modified_by.email,
                },
                {
                    "id": str(theme_b.id),
                    "name": "Theme B",
                    "description": theme_b.description,
                    "version": 1,
                    "modified_at": isoformat(theme_b.modified_at),
                    "last_modified_by": theme_b.last_modified_by.email,
                },
            ],
        }

    def test_create_selected_theme(self, client, staff_user, staff_user_token, free_text_question):
        url = reverse(
            "selected-theme-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        response = client.post(
            url,
            data=json.dumps({"name": "Test theme", "description": "Theme created from test"}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 201
        assert response.json().get("version") == 1

        selected_theme = SelectedTheme.objects.get(pk=response.json().get("id"))

        assert selected_theme.name == "Test theme"
        assert selected_theme.description == "Theme created from test"
        assert selected_theme.question == free_text_question
        assert selected_theme.version == 1
        assert selected_theme.last_modified_by == staff_user

    def test_patch_selected_theme__version_matches(
        self,
        client,
        staff_user,
        staff_user_token,
        non_staff_user,
        free_text_question,
        theme_a,
    ):
        assert theme_a.name != "Updated name"
        assert theme_a.description != "Updated description"
        assert theme_a.version == 2
        assert theme_a.last_modified_by is staff_user

        url = reverse(
            "selected-theme-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": theme_a.id,
            },
        )

        response = client.patch(
            url,
            data=json.dumps({"name": "Updated name", "description": "Updated description"}),
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {staff_user_token}",
                "If-Match": str(theme_a.version),
            },
        )

        assert response.status_code == 200
        assert response.json().get("version") == 3

        selected_theme = SelectedTheme.objects.get(pk=response.json().get("id"))

        assert selected_theme.name == "Updated name"
        assert selected_theme.description == "Updated description"
        assert selected_theme.version == 3
        assert selected_theme.last_modified_by == staff_user
        assert selected_theme.modified_at > theme_a.modified_at

    def test_patch_selected_theme__version_missing(
        self, client, staff_user_token, free_text_question, theme_a
    ):
        assert theme_a.name != "Updated name"
        assert theme_a.description != "Updated description"

        url = reverse(
            "selected-theme-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": theme_a.id,
            },
        )

        response = client.patch(
            url,
            data=json.dumps({"name": "Updated name", "description": "Updated description"}),
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {staff_user_token}",
            },
        )

        assert response.status_code == 428

        selected_theme = SelectedTheme.objects.get(pk=theme_a.id)

        assert selected_theme.name == theme_a.name
        assert selected_theme.description == theme_a.description

    def test_patch_selected_theme__version_invalid(
        self, client, staff_user_token, free_text_question, theme_a
    ):
        assert theme_a.name != "Updated name"
        assert theme_a.description != "Updated description"

        url = reverse(
            "selected-theme-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": theme_a.id,
            },
        )

        response = client.patch(
            url,
            data=json.dumps({"name": "Updated name", "description": "Updated description"}),
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {staff_user_token}",
                "If-Match": "1.1",
            },
        )

        assert response.status_code == 400

        selected_theme = SelectedTheme.objects.get(pk=theme_a.id)

        assert selected_theme.name == theme_a.name
        assert selected_theme.description == theme_a.description

    def test_patch_selected_theme__version_mismatch(
        self,
        client,
        free_text_question,
        theme_a,
        staff_user,
        staff_user_token,
    ):
        assert theme_a.name != "Updated name"
        assert theme_a.description != "Updated description"
        assert theme_a.version == 2
        assert theme_a.last_modified_by == staff_user

        url = reverse(
            "selected-theme-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": theme_a.id,
            },
        )

        response = client.patch(
            url,
            data=json.dumps({"name": "Updated name", "description": "Updated description"}),
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {staff_user_token}",
                "If-Match": "1",
            },
        )

        assert response.status_code == 412
        assert response.json().get("latest_version") == "2"
        assert response.json().get("last_modified_by") == {"email": staff_user.email}

        selected_theme = SelectedTheme.objects.get(pk=theme_a.id)

        assert selected_theme.name == theme_a.name
        assert selected_theme.description == theme_a.description

    def test_delete_selected_theme__version_matches(
        self, client, staff_user_token, free_text_question, selected_candidate_theme
    ):
        selected_theme = selected_candidate_theme.selectedtheme
        assert selected_theme is not None

        url = reverse(
            "selected-theme-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": selected_theme.id,
            },
        )

        response = client.delete(
            url,
            headers={
                "Authorization": f"Bearer {staff_user_token}",
                "If-Match": str(selected_theme.version),
            },
        )

        assert response.status_code == 204
        assert not SelectedTheme.objects.filter(pk=selected_theme.id).exists()

        selected_candidate_theme.refresh_from_db()
        assert selected_candidate_theme.selectedtheme is None

    def test_delete_selected_theme__version_missing(
        self, client, staff_user_token, free_text_question, selected_candidate_theme
    ):
        selected_theme = selected_candidate_theme.selectedtheme

        url = reverse(
            "selected-theme-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": selected_theme.id,
            },
        )

        response = client.delete(
            url,
            headers={
                "Authorization": f"Bearer {staff_user_token}",
            },
        )

        assert response.status_code == 428
        assert SelectedTheme.objects.filter(pk=selected_theme.id).exists()

    def test_delete_selected_theme__version_invalid(
        self, client, staff_user_token, free_text_question, selected_candidate_theme
    ):
        selected_theme = selected_candidate_theme.selectedtheme

        url = reverse(
            "selected-theme-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": selected_theme.id,
            },
        )

        response = client.delete(
            url,
            headers={
                "Authorization": f"Bearer {staff_user_token}",
                "If-Match": "1.1",
            },
        )

        assert response.status_code == 400
        assert SelectedTheme.objects.filter(pk=selected_theme.id).exists()

    def test_delete_selected_theme__version_mismatch(
        self,
        client,
        free_text_question,
        selected_candidate_theme,
        staff_user,
        staff_user_token,
    ):
        selected_theme = selected_candidate_theme.selectedtheme
        assert selected_theme.version == 2
        assert selected_theme.last_modified_by == staff_user

        url = reverse(
            "selected-theme-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": selected_theme.id,
            },
        )

        response = client.delete(
            url,
            headers={
                "Authorization": f"Bearer {staff_user_token}",
                "If-Match": "1",
            },
        )

        assert response.status_code == 412
        assert response.json().get("latest_version") == "2"
        assert response.json().get("last_modified_by") == {
            "email": staff_user.email,
        }
        assert SelectedTheme.objects.filter(pk=selected_theme.id).exists()

    def test_delete_selected_theme__not_found(
        self,
        client,
        free_text_question,
        staff_user_token,
    ):
        url = reverse(
            "selected-theme-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
                "pk": uuid4(),
            },
        )

        response = client.delete(
            url,
            headers={
                "Authorization": f"Bearer {staff_user_token}",
                "If-Match": "1",
            },
        )

        assert response.status_code == 404
