import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestRespondentViewSet:
    def test_get_respondent_list(
        self, client, consultation, respondent_1, respondent_2, staff_user_token
    ):
        url = reverse(
            "respondent-list",
            kwargs={"consultation_pk": consultation.id},
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 2
        assert response.json()["results"][0]["demographics"]
        assert response.json()["results"][1]["demographics"]

    def test_get_respondent_query_themefinder_id(
        self, client, consultation, respondent_1, respondent_2, staff_user_token
    ):
        url = reverse(
            "respondent-list",
            kwargs={"consultation_pk": consultation.id},
        )

        response = client.get(
            url,
            query_params={"themefinder_id": respondent_1.themefinder_id},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["results"][0]["id"] == str(respondent_1.id)

    def test_get_respondent_query_themefinder_range(
        self,
        client,
        consultation,
        respondent_1,
        respondent_2,
        respondent_3,
        respondent_4,
        staff_user_token,
    ):
        url = reverse(
            "respondent-list",
            kwargs={"consultation_pk": consultation.id},
        )

        response = client.get(
            url,
            query_params={"themefinder_id__gte": 2, "themefinder_id__lte": 4},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 3
        actual_respondents = {x["id"] for x in response.json()["results"]}
        expected_respondents = {str(respondent_2.id), str(respondent_3.id), str(respondent_4.id)}
        assert actual_respondents == expected_respondents

    def test_get_respondent_detail(
        self, client, consultation, respondent_1, respondent_2, staff_user_token
    ):
        url = reverse(
            "respondent-detail",
            kwargs={
                "consultation_pk": consultation.id,
                "pk": respondent_1.id,
            },
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["id"] == str(respondent_1.id)

    def test_patch_respondent_detail(self, client, staff_user_token, respondent_1):
        """we can update a respondents name"""
        url = reverse(
            "respondent-detail",
            kwargs={
                "consultation_pk": respondent_1.consultation.id,
                "pk": respondent_1.id,
            },
        )

        assert respondent_1.name is None
        response = client.patch(
            url,
            content_type="application/json",
            data={"name": "mr lebowski"},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "mr lebowski"
        respondent_1.refresh_from_db()
        assert respondent_1.name == "mr lebowski"

    def test_patch_respondent_detail_read_only_field_ignored(
        self, client, staff_user_token, respondent_1
    ):
        """we cannot update a respondents themefinder_id"""

        url = reverse(
            "respondent-detail",
            kwargs={
                "consultation_pk": respondent_1.consultation.id,
                "pk": respondent_1.id,
            },
        )

        assert respondent_1.themefinder_id == 1
        response = client.patch(
            url,
            content_type="application/json",
            data={"themefinder_id": 100},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        # note: DRF just ignores attempts to update read-only (editable=False) fields
        # we can change this behaviour but given that our frontend is the only consumer of this
        # API it doesnt seem worth it
        assert response.status_code == 200
        assert response.json()["themefinder_id"] == 1
        respondent_1.refresh_from_db()
        assert respondent_1.themefinder_id == 1
