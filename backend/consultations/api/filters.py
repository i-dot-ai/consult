from django.db.models import Count
from django_filters import CharFilter, UUIDFilter
from django_filters.rest_framework import BaseInFilter, BooleanFilter, FilterSet
from pgvector.django import CosineDistance
from rest_framework import serializers
from rest_framework.filters import SearchFilter

from authentication.models import User
from consultations.models import DemographicOption, Response
from embeddings import embed_text


class ResponseFilter(FilterSet):
    # TODO: adjust the frontend to match sensible DRF defaults
    sentimentFilters = BaseInFilter(field_name="annotation__sentiment", lookup_expr="in")
    evidenceRich = BooleanFilter(field_name="annotation__evidence_rich")
    unseenResponsesOnly = BaseInFilter(method="filter_seen", lookup_expr="in")
    themeFilters = BaseInFilter(method="filter_themes", lookup_expr="in")
    demographics = BaseInFilter(method="filter_demographics", lookup_expr="in")
    is_flagged = BooleanFilter()
    multiple_choice_answer = BaseInFilter(method="filter_multiple_choice", lookup_expr="in")
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
        """OR within each demographic group, AND across groups. Uses subquery to avoid JOINs."""
        if not value:
            return queryset

        from consultations.models import Respondent

        options = DemographicOption.objects.filter(id__in=value)
        groups = {}
        for option in options:
            groups.setdefault(option.field_name, []).append(option.id)

        # Build a respondent queryset that satisfies all groups (AND across, OR within)
        respondents = Respondent.objects.all()
        for group_ids in groups.values():
            respondents = respondents.filter(demographics__in=group_ids)

        return queryset.filter(respondent_id__in=respondents.values("id"))

    def filter_multiple_choice(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(chosen_options__in=value).distinct()

    class Meta:
        model = Response
        fields = ["respondent_id", "chosen_options"]


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
        fields = ["consultation_id"]


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
