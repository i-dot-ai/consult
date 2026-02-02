import resource
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import QuerySet
from django_rq import job

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

# Fields to exclude when cloning most records
_EXCLUDED_FIELDS = ["id", "created_at", "modified_at"]

# Fields to exclude when cloning history records
_HISTORY_EXCLUDED_FIELDS = ["history_id"]

# Clone database objects in batches to avoid memory limit
_BATCH_SIZE = 1000


def _clone(
    queryset: QuerySet,
    fk_mappings: list[tuple[str, dict[UUID, UUID]]],
    excluded_fields: list[str] = _EXCLUDED_FIELDS,
) -> dict[UUID, UUID]:
    """
    Clone all objects from queryset with updated foreign keys.

    Args:
        queryset: QuerySet of objects to clone
        fk_mappings: List of [ field_name, {old_id: new_id} ] for remapping foreign keys
        excluded_fields: Fields to exclude from cloning (defaults to _EXCLUDED_FIELDS)

    Returns:
        Dict mapping original IDs to cloned IDs
    """
    model = queryset.model
    id_map = {}
    total = queryset.count()
    offset = 0

    while offset < total:
        batch = queryset.order_by("pk").values()[offset : offset + _BATCH_SIZE]
        batch_ids = []
        batch_clones = []

        for original in batch:
            clone = {k: v for k, v in original.items() if k not in excluded_fields}

            for field_name, mapping in fk_mappings:
                old_value = original[field_name]
                new_value = mapping.get(old_value)
                if old_value is not None and new_value is None:
                    logger.warning(
                        f"_clone: {model.__name__}.{field_name} = {old_value} not found in mapping"
                    )
                clone[field_name] = new_value

            batch_ids.append(original["id"])
            batch_clones.append(model(**clone))

        created = model.objects.bulk_create(batch_clones)
        for i, orig_id in enumerate(batch_ids):
            id_map[orig_id] = created[i].id

        offset += _BATCH_SIZE
        rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)
        logger.info(
            f"_clone: {model.__name__} batch complete, {len(id_map)}/{total} cloned so far, "
            f"peak RSS: {rss_mb:.0f} MB"
        )

    logger.info(f"_clone: cloned {len(id_map)} {model.__name__} objects total")
    return id_map


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
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024)
    logger.info(f"clone_consultation: starting, peak RSS: {rss_mb:.0f} MB")

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
    annotation_theme_map = _clone(
        ResponseAnnotationTheme.objects.filter(
            response_annotation__response__question__consultation=original
        ),
        [("response_annotation_id", annotation_map), ("theme_id", selected_theme_map)],
    )

    # Clone historical records for ResponseAnnotation and ResponseAnnotationTheme
    _clone(
        ResponseAnnotation.history.model.objects.filter(id__in=annotation_map.keys()),
        [("id", annotation_map), ("response_id", response_map)],
        excluded_fields=_HISTORY_EXCLUDED_FIELDS,
    )
    _clone(
        ResponseAnnotationTheme.history.model.objects.filter(id__in=annotation_theme_map.keys()),
        [
            ("id", annotation_theme_map),
            ("response_annotation_id", annotation_map),
            ("theme_id", selected_theme_map),
        ],
        excluded_fields=_HISTORY_EXCLUDED_FIELDS,
    )

    return cloned


@job("default", timeout=3600)
def clone_consultation_job(consultation_id: UUID) -> UUID:
    """
    RQ job wrapper for clone_consultation.
    """
    original = Consultation.objects.get(id=consultation_id)
    cloned = clone_consultation(original)
    logger.info(f"Successfully cloned consultation {original.id} to {cloned.id}")
    return cloned.id
