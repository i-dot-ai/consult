from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from consultations.models import DemographicOption, Respondent
from factories import ConsultationFactory, RespondentFactory, UserFactory


def merge_url(consultation):
    return reverse(
        "demographic-option-v2-merge",
        kwargs={"consultation_pk": consultation.id},
    )


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
def test_merge_demographics_retains_first_option_and_relinks_distinct_respondents(
    client, consultation, non_staff_user_token
):
    retained = option(consultation, "Region", "North East")
    discarded = option(consultation, "Area", "North West")
    unrelated = option(consultation, "Age", "18-35")
    retained_only = RespondentFactory(consultation=consultation)
    discarded_only = RespondentFactory(consultation=consultation)
    both = RespondentFactory(consultation=consultation)
    unrelated_respondent = RespondentFactory(consultation=consultation)
    retained_only.demographics.add(retained)
    discarded_only.demographics.add(discarded)
    both.demographics.add(retained, discarded)
    unrelated_respondent.demographics.add(unrelated)

    response = client.post(
        merge_url(consultation),
        data={
            "new_value": "North",
            "demographic_options": [str(retained.id), str(discarded.id)],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": str(retained.id),
        "name": "Region",
        "value": "North",
        "count": 3,
    }
    retained.refresh_from_db()
    assert retained.field_name == "Region"
    assert retained.field_value == "North"
    assert retained.response_count == 3
    assert not DemographicOption.objects.filter(id=discarded.id).exists()
    assert set(retained.respondent_set.values_list("id", flat=True)) == {
        retained_only.id,
        discarded_only.id,
        both.id,
    }
    assert unrelated_respondent.demographics.get() == unrelated
    assert Respondent.objects.filter(consultation=consultation).count() == 4


@pytest.mark.django_db
def test_merge_demographics_preserves_request_order_for_retained_option(
    client, consultation, non_staff_user_token
):
    first_created = option(consultation, "Region", "First")
    retained = option(consultation, "Region", "Second")

    response = client.post(
        merge_url(consultation),
        data={
            "new_value": "Merged",
            "demographic_options": [str(retained.id), str(first_created.id)],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(retained.id)
    assert DemographicOption.objects.filter(id=retained.id, field_value="Merged").exists()
    assert not DemographicOption.objects.filter(id=first_created.id).exists()


@pytest.mark.django_db
def test_merge_demographics_merges_more_than_two_options(
    client, consultation, non_staff_user_token
):
    options = [option(consultation, "Region", value) for value in ["North", "South", "West"]]
    respondents = [RespondentFactory(consultation=consultation) for _ in options]
    for respondent, demographic_option in zip(respondents, options, strict=True):
        respondent.demographics.add(demographic_option)

    response = client.post(
        merge_url(consultation),
        data={
            "new_value": "All regions",
            "demographic_options": [str(value.id) for value in options],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 3
    assert DemographicOption.objects.filter(consultation=consultation).count() == 1


@pytest.mark.django_db
def test_merge_demographics_allows_target_name_from_discarded_option(
    client, consultation, non_staff_user_token
):
    retained = option(consultation, "Region", "North East")
    discarded = option(consultation, "Region", "North")

    response = client.post(
        merge_url(consultation),
        data={
            "new_value": "North",
            "demographic_options": [str(retained.id), str(discarded.id)],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert DemographicOption.objects.filter(id=retained.id, field_value="North").exists()
    assert not DemographicOption.objects.filter(id=discarded.id).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "demographic_options",
    [[], ["one"], ["duplicate", "duplicate"]],
)
def test_merge_demographics_rejects_invalid_option_lists(
    client, consultation, non_staff_user_token, demographic_options
):
    if demographic_options == ["one"]:
        demographic_options = [str(option(consultation, "Region", "North").id)]
    elif demographic_options == ["duplicate", "duplicate"]:
        option_id = str(option(consultation, "Region", "North").id)
        demographic_options = [option_id, option_id]

    response = client.post(
        merge_url(consultation),
        data={"new_value": "Merged", "demographic_options": demographic_options},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert "demographic_options" in response.json()


@pytest.mark.django_db
def test_merge_demographics_rejects_option_from_another_consultation(
    client, consultation, non_staff_user_token
):
    retained = option(consultation, "Region", "North")
    other = option(ConsultationFactory(), "Region", "South")

    response = client.post(
        merge_url(consultation),
        data={
            "new_value": "Merged",
            "demographic_options": [str(retained.id), str(other.id)],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert DemographicOption.objects.filter(id=retained.id, field_value="North").exists()
    assert DemographicOption.objects.filter(id=other.id).exists()


@pytest.mark.django_db
def test_merge_demographics_rejects_target_collision_outside_merge(
    client, consultation, non_staff_user_token
):
    retained = option(consultation, "Region", "North East")
    discarded = option(consultation, "Region", "North West")
    existing = option(consultation, "Region", "North")

    response = client.post(
        merge_url(consultation),
        data={
            "new_value": "North",
            "demographic_options": [str(retained.id), str(discarded.id)],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert DemographicOption.objects.filter(id=retained.id, field_value="North East").exists()
    assert DemographicOption.objects.filter(id=discarded.id).exists()
    assert DemographicOption.objects.filter(id=existing.id).exists()


@pytest.mark.django_db
def test_merge_demographics_rolls_back_when_rename_fails(
    client, consultation, non_staff_user_token
):
    retained = option(consultation, "Region", "North East")
    discarded = option(consultation, "Region", "North West")
    respondent = RespondentFactory(consultation=consultation)
    respondent.demographics.add(discarded)

    with (
        patch(
            "consultations.services.demographics.DemographicOption.save",
            side_effect=RuntimeError("save failed"),
        ),
        pytest.raises(RuntimeError, match="save failed"),
    ):
        client.post(
            merge_url(consultation),
            data={
                "new_value": "North",
                "demographic_options": [str(retained.id), str(discarded.id)],
            },
            content_type="application/json",
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert DemographicOption.objects.filter(id=discarded.id).exists()
    assert respondent.demographics.filter(id=discarded.id).exists()
    assert not respondent.demographics.filter(id=retained.id).exists()


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
def test_demographic_mutations_reject_unassigned_user(client, consultation):
    retained = option(consultation, "Region", "North")
    discarded = option(consultation, "Region", "South")
    user = UserFactory(is_staff=False)
    token = str(RefreshToken.for_user(user).access_token)

    merge_response = client.post(
        merge_url(consultation),
        data={
            "new_value": "Merged",
            "demographic_options": [str(retained.id), str(discarded.id)],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )
    update_response = client.patch(
        update_url(consultation, retained),
        data={"new_value": "Renamed"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert merge_response.status_code == 403
    assert update_response.status_code == 403
