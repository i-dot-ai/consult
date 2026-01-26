from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet

from backend.consultations.models import (
    CandidateTheme,
    Consultation,
    CrossCuttingTheme,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)

logger = settings.LOGGER

# Fields that should always be excluded when cloning
_EXCLUDED_FIELDS = ["id", "created_at", "modified_at"]


def _clone(
    queryset: QuerySet,
    fk_mappings: list[tuple[str, dict[UUID, UUID]]],
) -> dict[UUID, UUID]:
    """
    Clone all objects from queryset with updated foreign keys.

    Args:
        queryset: QuerySet of objects to clone
        fk_mappings: List of [ field_name, {old_id: new_id} ] for remapping foreign keys

    Returns:
        Dict mapping original IDs to cloned Ids
    """
    model = queryset.model
    originals = list(queryset.values())
    clones = []

    logger.info(f"_clone: cloning {len(originals)} {model.__name__} objects")

    for original in originals:
        clone = {k: v for k, v in original.items() if k not in _EXCLUDED_FIELDS}

        for field_name, mapping in fk_mappings:
            old_value = original[field_name]
            new_value = mapping.get(old_value)
            if old_value is not None and new_value is None:
                logger.warning(
                    f"_clone: {model.__name__}.{field_name} = {old_value} not found in mapping"
                )
            clone[field_name] = new_value

        clones.append(model(**clone))

    created = model.objects.bulk_create(clones)

    return {original["id"]: created[i].id for i, original in enumerate(originals)}


def _clone_candidate_themes(
    queryset: QuerySet,
    fk_mappings: list[tuple[str, dict[UUID, UUID]]],
) -> dict[UUID, UUID]:
    """
    Clone candidate themes maintaining self-referential parent FK.
    """
    candidate_theme_map = _clone(queryset, fk_mappings)

    cloned_themes = CandidateTheme.objects.filter(id__in=candidate_theme_map.values())

    updates = []
    for cloned_theme in list(cloned_themes):
        if cloned_theme.parent_id:
            cloned_theme.parent_id = candidate_theme_map[cloned_theme.parent_id]
            updates.append(cloned_theme)

    if updates:
        CandidateTheme.objects.bulk_update(updates, ["parent_id"])

    return candidate_theme_map


@transaction.atomic
def clone_consultation(original: Consultation) -> Consultation:
    """
    Clone a consultation including all related objects (with the
    exception of users).
    """
    # Clone consultation and give the same users access
    cloned = Consultation.objects.create(
        title=f"{original.title} (Clone)",
        code="",
        stage=original.stage,
    )
    cloned.users.set(original.users.all())
    consultation_map = {original.id: cloned.id}

    # Clone respondents, demographicoptions and respondent_demographics
    respondent_map = _clone(
        Respondent.objects.filter(consultation=original),
        [("consultation_id", consultation_map)],
    )
    demographic_map = _clone(
        DemographicOption.objects.filter(consultation=original),
        [("consultation_id", consultation_map)],
    )
    _clone(
        Respondent.demographics.through.objects.filter(respondent__consultation=original),
        [("respondent_id", respondent_map), ("demographicoption_id", demographic_map)],
    )

    # Clone questions and mulitchoiceanswers
    question_map = _clone(
        Question.objects.filter(consultation=original),
        [("consultation_id", consultation_map)],
    )
    multi_choice_map = _clone(
        MultiChoiceAnswer.objects.filter(question__consultation=original),
        [("question_id", question_map)],
    )

    # Clone crosscuttingthemes, selectedthemes and candidatethemes
    cross_cutting_theme_map = _clone(
        CrossCuttingTheme.objects.filter(consultation=original),
        [("consultation_id", consultation_map)],
    )
    selected_theme_map = _clone(
        SelectedTheme.objects.filter(question__consultation=original),
        [("question_id", question_map), ("crosscuttingtheme_id", cross_cutting_theme_map)],
    )
    _clone_candidate_themes(
        CandidateTheme.objects.filter(question__consultation=original),
        [("question_id", question_map), ("selectedtheme_id", selected_theme_map)],
    )

    # Clone responses and response_chosen_options
    response_map = _clone(
        Response.objects.filter(question__consultation=original),
        [("question_id", question_map), ("respondent_id", respondent_map)],
    )
    _clone(
        Response.chosen_options.through.objects.filter(response__question__consultation=original),
        [("response_id", response_map), ("multichoiceanswer_id", multi_choice_map)],
    )

    # Clone responseannotations and responseannotationthemes
    annotation_map = _clone(
        ResponseAnnotation.objects.filter(response__question__consultation=original),
        [("response_id", response_map)],
    )
    _clone(
        ResponseAnnotationTheme.objects.filter(
            response_annotation__response__question__consultation=original
        ),
        [("response_annotation_id", annotation_map), ("theme_id", selected_theme_map)],
    )

    return cloned
