import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from consultations.models import DemographicOption
from factories import ConsultationFactory, UserFactory


def update_url(consultation, option):
    return reverse(
        "demographic-option-v2-detail",
        kwargs={"consultation_pk": consultation.id, "pk": option.id},
    )


def list_url(consultation):
    return reverse(
        "demographic-option-v2-list",
        kwargs={"consultation_pk": consultation.id},
    )


def option(consultation, field_name, field_value):
    return DemographicOption.objects.create(
        consultation=consultation,
        field_name=field_name,
        field_value=field_value,
    )


@pytest.mark.django_db
def test_demographic_option_crud_is_scoped_to_consultation(
    client, consultation, non_staff_user_token
):
    existing = option(consultation, "Region", "North")
    option(ConsultationFactory(), "Region", "South")

    list_response = client.get(
        list_url(consultation),
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )
    create_response = client.post(
        list_url(consultation),
        data={"name": "Age", "value": "18-35"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["results"]] == [str(existing.id)]
    assert create_response.status_code == 201
    assert create_response.json()["name"] == "Age"
    created = DemographicOption.objects.get(id=create_response.json()["id"])
    assert created.consultation == consultation

    delete_response = client.delete(
        update_url(consultation, created),
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert delete_response.status_code == 204
    assert not DemographicOption.objects.filter(id=created.id).exists()


@pytest.mark.django_db
def test_update_demographic_option_renames_field_value(client, consultation, non_staff_user_token):
    demographic_option = option(consultation, "Region", "North East")
    demographic_option.response_count = 4
    demographic_option.save(update_fields=["response_count"])

    response = client.patch(
        update_url(consultation, demographic_option),
        data={"new_value": "North"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": str(demographic_option.id),
        "name": "Region",
        "value": "North",
        "count": 4,
    }


@pytest.mark.django_db
def test_update_demographic_option_rejects_option_from_another_consultation(
    client, consultation, non_staff_user_token
):
    other = option(ConsultationFactory(), "Region", "North")

    response = client.patch(
        update_url(consultation, other),
        data={"new_value": "Renamed"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 404
    assert DemographicOption.objects.filter(id=other.id, field_value="North").exists()


@pytest.mark.django_db
def test_update_demographic_option_rejects_target_collision(
    client, consultation, non_staff_user_token
):
    demographic_option = option(consultation, "Region", "North East")
    option(consultation, "Region", "North")

    response = client.patch(
        update_url(consultation, demographic_option),
        data={"new_value": "North"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert DemographicOption.objects.filter(
        id=demographic_option.id, field_value="North East"
    ).exists()


@pytest.mark.django_db
def test_demographic_option_mutations_reject_unassigned_user(client, consultation):
    demographic_option = option(consultation, "Region", "North")
    user = UserFactory(is_staff=False)
    token = str(RefreshToken.for_user(user).access_token)

    response = client.patch(
        update_url(consultation, demographic_option),
        data={"new_value": "Renamed"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
