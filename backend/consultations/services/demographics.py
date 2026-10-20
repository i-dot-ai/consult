from collections.abc import Sequence
from uuid import UUID

from django.db import transaction

from consultations.models import Consultation, DemographicOption, Respondent


class DemographicOptionError(ValueError):
    pass


def _get_options_by_id(
    consultation: Consultation, option_ids: Sequence[UUID]
) -> dict[UUID, DemographicOption]:
    options = DemographicOption.objects.select_for_update().filter(
        consultation=consultation,
        id__in=option_ids,
    )
    options_by_id = {option.id: option for option in options}
    if len(options_by_id) != len(option_ids):
        raise DemographicOptionError(
            "All demographic options must exist and belong to this consultation."
        )
    return options_by_id


def _validate_target_value(
    retained: DemographicOption, selected_ids: Sequence[UUID], new_value: str
) -> None:
    if (
        DemographicOption.objects.select_for_update()
        .filter(
            consultation=retained.consultation,
            field_name=retained.field_name,
            field_value=new_value,
        )
        .exclude(id__in=selected_ids)
        .exists()
    ):
        raise DemographicOptionError(
            "A demographic option with this name already exists. Include it in the merge."
        )


@transaction.atomic
def merge_demographic_options(
    consultation: Consultation, option_ids: Sequence[UUID], new_value: str
) -> DemographicOption:
    consultation = Consultation.objects.select_for_update().get(pk=consultation.pk)
    options_by_id = _get_options_by_id(consultation, option_ids)
    retained = options_by_id[option_ids[0]]
    discarded_ids = option_ids[1:]
    _validate_target_value(retained, option_ids, new_value)

    respondent_demographics = Respondent.demographics.through
    respondent_ids = list(
        respondent_demographics.objects.filter(demographicoption_id__in=option_ids)
        .values_list("respondent_id", flat=True)
        .distinct()
    )
    respondent_demographics.objects.bulk_create(
        [
            respondent_demographics(
                respondent_id=respondent_id,
                demographicoption_id=retained.id,
            )
            for respondent_id in respondent_ids
        ],
        ignore_conflicts=True,
    )

    DemographicOption.objects.filter(id__in=discarded_ids).delete()
    retained.field_value = new_value
    retained.response_count = respondent_demographics.objects.filter(
        demographicoption_id=retained.id
    ).count()
    retained.save(update_fields=["field_value", "response_count", "modified_at"])
    return retained


@transaction.atomic
def update_demographic_option(
    consultation: Consultation, option_id: UUID, new_value: str
) -> DemographicOption:
    consultation = Consultation.objects.select_for_update().get(pk=consultation.pk)
    option = _get_options_by_id(consultation, [option_id])[option_id]
    _validate_target_value(option, [option_id], new_value)
    option.field_value = new_value
    option.save(update_fields=["field_value", "modified_at"])
    return option
