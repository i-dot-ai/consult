from collections import defaultdict
from typing import ClassVar
from uuid import UUID

from django.conf import settings
from django.db.models import Count
from django_filters import CharFilter, UUIDFilter
from django_filters.rest_framework import BaseInFilter, BooleanFilter, FilterSet
from pgvector.django import CosineDistance
from rest_framework import serializers
from rest_framework.filters import SearchFilter

from authentication.models import User
from consultations.models import DemographicOption, Response
from consultations.query_params import RepeatedValueFilter, is_uuid
from consultations.services.closed_answers import (
    filter_responses_by_answers,
    filter_responses_by_demographic_answers,
    split_demographic_answer_id,
)
from embeddings import embed_text

logger = settings.LOGGER


class ResponseFilter(FilterSet):
    # TODO: adjust the frontend to match sensible DRF defaults
    sentimentFilters = BaseInFilter(field_name="annotation__sentiment", lookup_expr="in")
    evidenceRich = BooleanFilter(field_name="annotation__evidence_rich")
    unseenResponsesOnly = BaseInFilter(method="filter_seen", lookup_expr="in")
    themeFilters = BaseInFilter(method="filter_themes", lookup_expr="in")
    demographics = BaseInFilter(method="filter_demographics", lookup_expr="in")
    is_flagged = BooleanFilter()
    multiple_choice_answer = BaseInFilter(method="filter_multiple_choice", lookup_expr="in")
    answers = RepeatedValueFilter(method="filter_answers")
    demographic_answers = RepeatedValueFilter(method="filter_demographic_answers")
    respondent_id = UUIDFilter()
    question_id = UUIDFilter()

    def filter_seen(self, queryset, name, value):
        """
        Filter responses based on whether they have been read by the current user.
        When unseenResponses=true, show only responses NOT read by the current user.
        When unseenResponses=false, show all responses (no filtering).
        """
        if not value or not self.request or not self.request.user.is_authenticated:
            return queryset

        try:
            show_unseen_only = (
                value[0].lower() == "true"
                if isinstance(value, list) and len(value) > 0
                else bool(value)
            )
        except (AttributeError, IndexError, ValueError):
            # Malformed filter value — fall back to no filtering rather than erroring.
            logger.warning(
                "Ignoring malformed unseenResponsesOnly filter value: {value}", value=value
            )
            return queryset

        if show_unseen_only:
            return queryset.exclude(read_by=self.request.user)
        else:
            return queryset

    def filter_themes(self, queryset, name, value):
        if not value:
            return queryset
        # Use single JOIN with HAVING clause for AND logic
        qs = (
            queryset.filter(annotation__themes__id__in=value)
            .annotate(matched_theme_count=Count("annotation__themes", distinct=True))
            .filter(matched_theme_count=len(value))
        )
        return qs

    def filter_demographics(self, queryset, name, value):
        """OR within each demographic group, AND across groups. Uses nested subqueries to avoid cross-joins."""
        if not value:
            return queryset

        answer_ids: list[str] = []
        option_ids: list[str] = []
        for item in value:
            if split_demographic_answer_id(item) is not None:
                answer_ids.append(item)
            else:
                option_ids.append(item)
        if answer_ids:
            queryset = self.filter_demographic_answers(queryset, name, answer_ids)
        if not option_ids:
            return queryset

        from consultations.models import Respondent

        options = DemographicOption.objects.filter(id__in=option_ids)
        groups = {}
        for option in options:
            groups.setdefault(option.field_name, []).append(option.id)

        # Each group narrows via a subquery rather than chaining M2M JOINs
        respondents = Respondent.objects.all()
        for group_ids in groups.values():
            respondents = respondents.filter(
                id__in=Respondent.objects.filter(demographics__in=group_ids).values("id")
            )

        return queryset.filter(respondent_id__in=respondents.values("id"))

    def filter_demographic_answers(self, queryset, name, value):
        selections: dict[UUID, list[str]] = defaultdict(list)
        for item in value:
            if (parsed := split_demographic_answer_id(item)) is not None:
                question_id, text = parsed
                selections[question_id].append(text)
        if not selections:
            return queryset
        return filter_responses_by_demographic_answers(queryset, selections)

    def filter_answers(self, queryset, name, value):
        if not value:
            return queryset
        return filter_responses_by_answers(queryset, value)

    def filter_multiple_choice(self, queryset, name, value):
        """Legacy option ids, or answer texts while the frontend still keys answers by id."""
        if not value:
            return queryset
        option_ids = [item for item in value if is_uuid(item)]
        texts = [item for item in value if not is_uuid(item)]
        if texts:
            queryset = filter_responses_by_answers(queryset, texts)
        if option_ids:
            queryset = queryset.filter(chosen_options__in=option_ids).distinct()
        return queryset

    class Meta:
        model = Response
        fields: ClassVar[list] = ["respondent_id"]


def apply_search_filter(queryset, query_params):
    """Apply keyword/semantic search to a response queryset."""
    search_value = query_params.get("searchValue")
    search_mode = query_params.get("searchMode")

    if not search_value:
        return queryset

    if search_mode == "keyword":
        return queryset.filter(free_text__icontains=search_value)
    elif search_mode == "semantic":
        embedded_query = embed_text(search_value)
        distance = CosineDistance("embedding", embedded_query)
        return queryset.annotate(distance=distance).order_by("distance")

    return queryset


def get_filtered_responses(query_params, consultation_id, question_id=None):
    """
    Single entry point for filtering responses. Used by all aggregation endpoints
    (question counts, themes, demographics) and the responses list.
    Applies filter params AND search.
    """
    queryset = Response.objects.filter(question__consultation_id=consultation_id)
    if question_id:
        queryset = queryset.filter(question_id=question_id)

    filterset = ResponseFilter(query_params, queryset=queryset)
    queryset = filterset.qs

    queryset = apply_search_filter(queryset, query_params)

    return queryset


def get_filtered_response_ids(query_params, consultation_id, question_id=None):
    """
    Like get_filtered_responses but materialises the IDs upfront.
    Use this for aggregation queries (counts, themes, demographics) where the filtered
    set is used as a subquery multiple times.
    """
    queryset = get_filtered_responses(query_params, consultation_id, question_id)
    return list(queryset.values_list("id", flat=True))


class UserFilter(FilterSet):
    email = CharFilter(field_name="email", lookup_expr="exact")
    is_in = BooleanFilter(method="filter_by_consultation")
    consultation_id = UUIDFilter(method="filter_by_consultation")

    def filter_by_consultation(self, queryset, name, value):
        consultation_id = self.request.GET.get("consultation_id")
        is_in = self.request.GET.get("is_in")

        if not consultation_id or is_in is None:
            return queryset

        is_in_bool = is_in.lower() == "true"

        if is_in_bool:
            return queryset.filter(consultation__id=consultation_id)
        else:
            return queryset.exclude(consultation__id=consultation_id)

    class Meta:
        model = User
        fields: ClassVar[list] = ["consultation_id"]


class ResponseSearchSerializer(serializers.Serializer):
    searchMode = serializers.ChoiceField(choices=["keyword"], required=False, default="keyword")
    searchValue = serializers.CharField(required=False)


class ResponseSearchFilter(SearchFilter):
    def filter_queryset(self, request, queryset, view):
        serializer = ResponseSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        search_value = request.query_params.get("searchValue")
        search_mode = request.query_params.get("searchMode")

        if not search_value:
            return queryset

        if search_mode == "keyword":
            return queryset.filter(free_text__icontains=search_value)
        elif search_mode == "semantic":
            embedded_query = embed_text(search_value)
            # distance: exact match = 0, exact opposite = 2
            distance = CosineDistance("embedding", embedded_query)
            return queryset.annotate(distance=distance).order_by("distance")
        else:
            return queryset
