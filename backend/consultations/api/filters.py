from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Avg, Count, F, StdDev
from django_filters import UUIDFilter
from django_filters.rest_framework import BaseInFilter, BooleanFilter, FilterSet
from pgvector.django import CosineDistance
from rest_framework import serializers
from rest_framework.filters import SearchFilter

from authentication.models import User
from consultations.models import Response
from embeddings import embed_text


class ResponseFilter(FilterSet):
    # TODO: adjust the frontend to match sensible DRF defaults
    sentimentFilters = BaseInFilter(field_name="annotation__sentiment", lookup_expr="in")
    evidenceRich = BooleanFilter(field_name="annotation__evidence_rich")
    unseenResponsesOnly = BaseInFilter(method="filter_seen", lookup_expr="in")
    themeFilters = BaseInFilter(method="filter_themes", lookup_expr="in")
    demographics = BaseInFilter(field_name="respondent__demographics", lookup_expr="in")
    is_flagged = BooleanFilter()
    multiple_choice_answer = BaseInFilter(field_name="chosen_options", lookup_expr="in")
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

    class Meta:
        model = Response
        fields = ["respondent_id", "chosen_options"]


class UserFilter(FilterSet):
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
    searchMode = serializers.ChoiceField(
        choices=["keyword", "semantic", "representative"], required=False
    )
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
        elif search_mode == "representative":
            embedded_query = embed_text(search_value)
            # semantic_score: exact match = 1, exact opposite = -1
            semantic_score = 1 - CosineDistance("embedding", embedded_query)

            search_query = SearchQuery(search_value)
            search_rank_score = SearchRank(F("search_vector"), search_query, normalization=32)

            hybrid_score = (0.9 * semantic_score) + (0.1 * search_rank_score)
            responses = queryset.annotate(
                hybrid_score=hybrid_score, semantic_score=semantic_score
            ).filter(semantic_score__gte=0.3)

            mean = responses.aggregate(Avg("hybrid_score"))["hybrid_score__avg"]
            std = responses.aggregate(StdDev("hybrid_score"))["hybrid_score__stddev"]
            if std is None or std == 0:
                return responses.order_by("-hybrid_score")

            return (
                responses.annotate(z_score=(F("hybrid_score") - mean) / std)
                .filter(z_score__gte=1)
                .order_by("-z_score")
            )
        else:
            return queryset
