import uuid
from typing import ClassVar

from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultations import models
from consultations.api_v2.demographic_tokens import encode_demographic_token
from consultations.api_v2.filters import (
    ResponseFilter,
    ResponseSearchFilter,
    get_filtered_response_ids,
)
from consultations.api_v2.pagination import ResponsePagination
from consultations.api_v2.permissions import CanSeeConsultationV2
from consultations.api_v2.serializers import (
    ResponseSerializer,
    ResponseThemeInformationSerializer,
    ThemeSerializer,
)
from consultations.services.closed_answers import closed_answer_rows

# Upper bound on how many responses a single bulk mark-read request may carry.
# This matches the maximum page size so a full page can always be marked at once,
# while still capping the work done per request.
MAX_BULK_MARK_READ = 1000

# v2 responses carry their content in Response.text; unanswered responses have
# no text (or an empty string). Used for listing and demographic aggregation.
ANSWERED_TEXT_FILTER = ~Q(text__isnull=True) & ~Q(text="")


class ResponseViewSet(ModelViewSet):
    serializer_class = ResponseSerializer
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2 | IsAdminUser]
    pagination_class = ResponsePagination
    filter_backends: ClassVar[list] = [ResponseSearchFilter]
    http_method_names: ClassVar[list] = ["get", "patch", "post"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        queryset = models.Response.objects.filter(question__consultation_id=consultation_uuid)

        # Support nesting under questions: /questions/{question_pk}/responses/
        question_pk = self.kwargs.get("question_pk")
        if question_pk:
            queryset = queryset.filter(question_id=question_pk)
            # Only return answered responses when listing under a question
            if self.action == "list":
                queryset = queryset.filter(ANSWERED_TEXT_FILTER)

        # Optimize queryset with select_related and prefetch_related
        queryset = queryset.select_related(
            "respondent",
            "annotation",
            "question",
        ).prefetch_related(
            # One prefetch serves the selected answers and the demographic data alike
            Prefetch(
                "respondent__response_set",
                queryset=closed_answer_rows(consultation_uuid),
                to_attr="prefetched_closed_answers",
            ),
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
        # themeFilters joins through the annotation themes and can duplicate rows; the answer
        # and demographic filters narrow by subquery and never do.
        if self.request.GET.get("themeFilters"):
            filtered_queryset = filtered_queryset.distinct()
        # Stable ordering is required for cursor-based pagination to be consistent
        # across pages. Without it PostgreSQL may return the same row on multiple
        # pages as the query plan shifts. The semantic-search filter overrides
        # this with .order_by("distance") when applied.
        return filtered_queryset.order_by("id")

    @action(
        detail=False,
        methods=["get"],
        url_path="demographic-options",
        url_name="demographic-options",
    )
    def demographic_options(self, request, consultation_pk=None, **kwargs):
        """Aggregate v2 demographic answers for the filter sidebar.

        Honors the same filter params/search as the responses list: the counted
        population is the respondents of the currently filtered responses. Returns
        the {id, name, value, count} shape the sidebar already consumes; `id` is an
        opaque demographic token (see api_v2.demographic_tokens) that can be passed
        straight back in the `?demographics=` filter param.
        """
        consultation_uuid = self.kwargs["consultation_pk"]
        filtered_response_ids = get_filtered_response_ids(self.request.GET, consultation_uuid)
        filtered_respondent_ids = models.Response.objects.filter(
            id__in=filtered_response_ids
        ).values("respondent_id")

        # v1 parity: every answer value of every demographic question stays listed
        # (zero-count values included under filters); counts cover only the
        # respondents of the currently filtered responses.
        aggregated = (
            models.Response.objects.filter(
                question__type=models.Question.QuestionType.DEMOGRAPHIC,
                question__consultation_id=consultation_uuid,
            )
            .filter(ANSWERED_TEXT_FILTER)
            .values("question_id", "question__text", "text")
            .annotate(
                count=Count(
                    "respondent_id",
                    distinct=True,
                    filter=Q(respondent_id__in=filtered_respondent_ids),
                )
            )
            .order_by("question__number", "-count", "text")
        )
        return Response(
            [
                {
                    "id": encode_demographic_token(row["question_id"], row["text"]),
                    "name": row["question__text"],
                    "value": row["text"],
                    "count": row["count"],
                }
                for row in aggregated
            ]
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="themes",
        permission_classes=[IsAuthenticated, CanSeeConsultationV2],
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
        permission_classes=[IsAuthenticated, CanSeeConsultationV2],
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
        permission_classes=[IsAuthenticated, CanSeeConsultationV2],
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

    @action(
        detail=False,
        methods=["post"],
        url_path="mark-read-bulk",
        permission_classes=[IsAuthenticated, CanSeeConsultationV2],
    )
    def mark_read_bulk(self, request, consultation_pk=None, **kwargs):
        """Mark multiple responses as read by the current user in a single request"""
        requested_response_ids = request.data.get("response_ids", [])
        if not requested_response_ids:
            return Response(
                {"message": "No response IDs provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(requested_response_ids) > MAX_BULK_MARK_READ:
            return Response(
                {"message": (f"Too many response IDs provided. Maximum is {MAX_BULK_MARK_READ}.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_response_ids = []
        for requested_id in requested_response_ids:
            try:
                valid_response_ids.append(uuid.UUID(str(requested_id)))
            except (ValueError, AttributeError):
                # Skip malformed IDs rather than failing the whole batch.
                continue

        # Restrict to responses that actually belong to this consultation (and, when
        # nested under a question, that question) so a user cannot mark responses
        # outside their access by passing arbitrary IDs.
        accessible_response_filter = {
            "id__in": valid_response_ids,
            "question__consultation_id": consultation_pk,
        }
        question_pk = self.kwargs.get("question_pk")
        if question_pk:
            accessible_response_filter["question_id"] = question_pk

        accessible_response_ids = models.Response.objects.filter(
            **accessible_response_filter
        ).values_list("id", flat=True)

        read_by_records = [
            models.ResponseReadBy(response_id=response_id, user=request.user)
            for response_id in accessible_response_ids
        ]
        # ignore_conflicts skips responses this user had already read. We don't report a
        # count: with ignore_conflicts=True, bulk_create returns every object passed in
        # (conflicting rows just have pk=None), so its length would overstate inserts.
        models.ResponseReadBy.objects.bulk_create(read_by_records, ignore_conflicts=True)

        return Response({"message": "Responses marked as read"})
