import json
from zoneinfo import ZoneInfo

import pytest
from django.conf import settings
from django.urls import reverse

from consultation_analyser.consultations.models import SelectedTheme


@pytest.mark.django_db
class TestSelectedThemeViewSet:
    def test_get_selected_themes(
        self, client, consultation_user_token, free_text_question, theme_a, theme_b
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
            headers={"Authorization": f"Bearer {consultation_user_token}"},
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
                    "version": 1,
                    "modified_at": theme_a.modified_at.astimezone(
                        ZoneInfo(settings.TIME_ZONE)
                    ).isoformat(),
                    "last_modified_by": None,
                },
                {
                    "id": str(theme_b.id),
                    "name": "Theme B",
                    "description": theme_b.description,
                    "version": 1,
                    "modified_at": theme_b.modified_at.astimezone(
                        ZoneInfo(settings.TIME_ZONE)
                    ).isoformat(),
                    "last_modified_by": theme_b.last_modified_by.email,
                },
            ],
        }

    def test_create_selected_theme(
        self, client, consultation_user, consultation_user_token, free_text_question
    ):
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
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 201
        assert response.json().get("version") == 1

        selected_theme = SelectedTheme.objects.get(pk=response.json().get("id"))

        assert selected_theme.name == "Test theme"
        assert selected_theme.description == "Theme created from test"
        assert selected_theme.question == free_text_question
        assert selected_theme.version == 1
        assert selected_theme.last_modified_by == consultation_user

    def test_patch_selected_theme__version_matches(
        self, client, consultation_user, consultation_user_token, free_text_question, theme_a
    ):
        assert theme_a.name != "Updated name"
        assert theme_a.description != "Updated description"
        assert theme_a.version == 1
        assert theme_a.last_modified_by is None

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
                "Authorization": f"Bearer {consultation_user_token}",
                "If-Match": str(theme_a.version),
            },
        )

        assert response.status_code == 200
        assert response.json().get("version") == 2

        selected_theme = SelectedTheme.objects.get(pk=response.json().get("id"))

        assert selected_theme.name == "Updated name"
        assert selected_theme.description == "Updated description"
        assert selected_theme.version == 2
        assert selected_theme.last_modified_by == consultation_user
        assert selected_theme.modified_at > theme_a.modified_at

    def test_patch_selected_theme__version_missing(
        self, client, consultation_user_token, free_text_question, theme_a
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
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )

        assert response.status_code == 428

        selected_theme = SelectedTheme.objects.get(pk=theme_a.id)

        assert selected_theme.name == theme_a.name
        assert selected_theme.description == theme_a.description

    def test_patch_selected_theme__version_invalid(
        self, client, consultation_user_token, free_text_question, theme_a
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
                "Authorization": f"Bearer {consultation_user_token}",
                "If-Match": "1.1",
            },
        )

        assert response.status_code == 400

        selected_theme = SelectedTheme.objects.get(pk=theme_a.id)

        assert selected_theme.name == theme_a.name
        assert selected_theme.description == theme_a.description

    def test_patch_selected_theme__version_mismatch(
        self, client, consultation_user_token, free_text_question, theme_a
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
                "Authorization": f"Bearer {consultation_user_token}",
                "If-Match": str(theme_a.version - 1),
            },
        )

        assert response.status_code == 412
        assert response.json().get("latest_version") == "1"

        selected_theme = SelectedTheme.objects.get(pk=theme_a.id)

        assert selected_theme.name == theme_a.name
        assert selected_theme.description == theme_a.description

    def test_delete_selected_theme__version_matches(
        self, client, consultation_user_token, free_text_question, selected_candidate_theme
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
                "Authorization": f"Bearer {consultation_user_token}",
                "If-Match": str(selected_theme.version),
            },
        )

        assert response.status_code == 204
        assert not SelectedTheme.objects.filter(pk=selected_theme.id).exists()

        selected_candidate_theme.refresh_from_db()
        assert selected_candidate_theme.selectedtheme is None

    def test_delete_selected_theme__version_missing(
        self, client, consultation_user_token, free_text_question, selected_candidate_theme
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
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )

        assert response.status_code == 428
        assert SelectedTheme.objects.filter(pk=selected_theme.id).exists()

    def test_delete_selected_theme__version_invalid(
        self, client, consultation_user_token, free_text_question, selected_candidate_theme
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
                "Authorization": f"Bearer {consultation_user_token}",
                "If-Match": "1.1",
            },
        )

        assert response.status_code == 400
        assert SelectedTheme.objects.filter(pk=selected_theme.id).exists()

    def test_delete_selected_theme__version_mismatch(
        self, client, consultation_user_token, free_text_question, selected_candidate_theme
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
                "Authorization": f"Bearer {consultation_user_token}",
                "If-Match": str(selected_theme.version - 1),
            },
        )

        assert response.status_code == 412
        assert response.json().get("latest_version") == "1"
        assert SelectedTheme.objects.filter(pk=selected_theme.id).exists()
