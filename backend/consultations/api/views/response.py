import uuid

from django.db.models import Exists, OuterRef
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultations import models
from consultations.api.filters import ResponseFilter, ResponseSearchFilter
from consultations.api.permissions import (
    CanSeeConsultation,
)
from consultations.api.serializers import (
    ResponseSerializer,
    ResponseThemeInformationSerializer,
    ThemeSerializer,
)


class BespokeResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_page_size(self, request):
        search_mode = request.query_params.get("searchMode")

        if search_mode == "representative":
            # We only want to return top 10 representative responses
            return min(10, self.max_page_size)
        else:
            return super().get_page_size(request)

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        page_size = self.get_page_size(request)
        cursor = request.query_params.get("cursor")
        self._is_semantic = request.query_params.get("searchMode") == "semantic"

        # COUNT only on first page — skipped on every subsequent load-more click.
        # On large consultations this avoids a repeated full-table count.
        self._filtered_count = queryset.count() if not cursor else None

        if cursor:
            if self._is_semantic:
                # Semantic search is ordered by distance with no stable row key,
                # so keyset pagination does not apply. Use an integer offset encoded
                # in the cursor instead.
                try:
                    semantic_offset = int(cursor)
                except ValueError:
                    semantic_offset = 0  # Malformed cursor — treat as first page
                self._semantic_offset = semantic_offset
                items = list(queryset[semantic_offset : semantic_offset + page_size + 1])
            else:
                # Keyset pagination: seek directly to the position after the last-seen id.
                self._semantic_offset = 0
                try:
                    uuid.UUID(cursor)  # validate before passing to the ORM
                    queryset = queryset.filter(id__gt=cursor)
                except ValueError:
                    pass  # Malformed cursor — treat as first page
                items = list(queryset[: page_size + 1])
        else:
            self._semantic_offset = 0
            items = list(queryset[: page_size + 1])

        self._has_next = len(items) > page_size
        self._page = items[:page_size] if self._has_next else items
        return self._page

    def get_paginated_response(self, data):
        if self._has_next and self._page:
            if self._is_semantic:
                next_cursor = str(self._semantic_offset + len(self._page))
            else:
                next_cursor = str(self._page[-1].id)
        else:
            next_cursor = None

        result = {
            "has_more_pages": self._has_next,
            "next_cursor": next_cursor,
            "all_respondents": data,
        }
        if self._filtered_count is not None:
            result["total_count"] = self._filtered_count
        return Response(result)


class ResponseViewSet(ModelViewSet):
    serializer_class = ResponseSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation]
    pagination_class = BespokeResultsSetPagination
    filter_backends = [ResponseSearchFilter]
    http_method_names = ["get", "patch", "post"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        queryset = models.Response.objects.filter(question__consultation_id=consultation_uuid)

        # Support nesting under questions: /questions/{question_pk}/responses/
        question_pk = self.kwargs.get("question_pk")
        if question_pk:
            queryset = queryset.filter(question_id=question_pk)
            # Only return responses with free text when listing under a question
            if self.action == "list":
                queryset = queryset.filter(free_text__isnull=False)

        # Optimize queryset with select_related and prefetch_related
        queryset = queryset.select_related(
            "respondent",
            "annotation",
            "question",
        ).prefetch_related(
            "chosen_options",
            "respondent__demographics",
            "annotation__responseannotationtheme_set__assigned_by",
            "annotation__responseannotationtheme_set",
            "annotation__responseannotationtheme_set__theme",
        )

        queryset = queryset.annotate(
            is_flagged=Exists(
                models.ResponseAnnotation.objects.filter(
                    response=OuterRef("pk"), flagged_by=self.request.user
                )
            ),
            is_read_by_user=Exists(
                models.Response.objects.filter(read_by=self.request.user, pk=OuterRef("pk"))
            ),
            annotation_is_edited=Exists(
                models.ResponseAnnotation.history.filter(
                    id=OuterRef("annotation__id"),
                    history_type="~",  # django-simple-history: '+' = created, '~' = updated, '-' = deleted see:https://django-simple-history.readthedocs.io/en/latest/quick_start.html#what-is-django-simple-history-doing-behind-the-scenes
                )
            ),
            # Safe to query live table: ResponseSerializer.update() always calls
            # annotation.save() after any theme change, so annotation_is_edited will be
            # True even if all human-assigned themes were subsequently removed.
            annotation_has_human_assigned_themes=Exists(
                models.ResponseAnnotationTheme.objects.filter(
                    response_annotation_id=OuterRef("annotation__id"),
                    assigned_by__isnull=False,
                )
            ),
        )
        # Apply additional FilterSet filtering (including themeFilters)
        filterset = ResponseFilter(self.request.GET, queryset=queryset, request=self.request)
        filtered_queryset = filterset.qs
        # Only use .distinct() when filters that JOIN through M2M are active —
        # these can produce duplicate rows.
        if (
            self.request.GET.get("themeFilters")
            or self.request.GET.get("demographics")
            or self.request.GET.get("multiple_choice_answer")
        ):
            filtered_queryset = filtered_queryset.distinct()
        # Stable ordering is required for cursor-based pagination to be consistent
        # across pages. Without it PostgreSQL may return the same row on multiple
        # pages as the query plan shifts. The semantic-search filter overrides
        # this with .order_by("distance") when applied.
        return filtered_queryset.order_by("id")

    @action(
        detail=True,
        methods=["get"],
        url_path="themes",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def themes(self, request, consultation_pk=None, pk=None):
        """Get themes for given responses"""
        response = self.get_object()

        all_themes = models.SelectedTheme.objects.filter(question=response.question)
        if response.question.consultation.display_ai_selected_themes:
            annotation, _ = models.ResponseAnnotation.objects.get_or_create(response=response)
            selected_themes = annotation.themes.all()
        else:
            selected_themes = []

        # Serialize the themes properly using ThemeSerializer
        all_themes_data = ThemeSerializer(all_themes, many=True).data
        selected_themes_data = ThemeSerializer(selected_themes, many=True).data

        serializer = ResponseThemeInformationSerializer(
            data={"selected_themes": selected_themes_data, "all_themes": all_themes_data}
        )
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["patch"],
        url_path="toggle-flag",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def toggle_flag(self, request, consultation_pk=None, pk=None):
        """Toggle flag on/off for the user"""
        response = self.get_object()
        if response.annotation.flagged_by.contains(request.user):
            response.annotation.flagged_by.remove(request.user)
        else:
            response.annotation.flagged_by.add(request.user)
        response.annotation.save()
        return Response()

    @action(
        detail=True,
        methods=["post"],
        url_path="mark-read",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def mark_read(self, request, consultation_pk=None, pk=None):
        """Mark this response as read by the current user"""
        response = self.get_object()

        # Check if already read before marking
        was_already_read = response.is_read_by(request.user)
        response.mark_as_read_by(request.user)

        return Response(
            {
                "message": "Response marked as read",
                "was_already_read": was_already_read,
            }
        )
