from time import time

from django.conf import settings
from django.db.models import Count, Prefetch
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultations import models
from consultations.api.permissions import (
    CanSeeConsultation,
)
from consultations.api.serializers import (
    QuestionSerializer,
    ThemeInformationSerializer,
)

logger = settings.LOGGER


class QuestionPagination(PageNumberPagination):
    page_size = 500


class QuestionViewSet(ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation]
    filterset_fields = ["has_free_text"]
    http_method_names = ["get", "patch", "delete"]
    pagination_class = QuestionPagination

    def list(self, request, *args, **kwargs):
        """Override list to add performance logging"""
        start_time = time()
        consultation_pk = kwargs.get('consultation_pk')

        logger.info(
            "Question list starting for consultation {consultation_id}",
            consultation_id=str(consultation_pk),
        )

        response = super().list(request, *args, **kwargs)

        duration_ms = int((time() - start_time) * 1000)
        # TODO: check me
        # question_count = len(response.data) if isinstance(response.data, list) else 0

        # Handle different response data structures
        if isinstance(response.data, list):
            question_count = len(response.data)
        elif isinstance(response.data, dict) and 'results' in response.data:
            question_count = len(response.data['results'])
        elif isinstance(response.data, dict) and 'count' in response.data:
            question_count = response.data['count']
        else:
            question_count = 0
            logger.warning(
                "Unexpected response data structure: {data_type}",
                data_type=type(response.data).__name__,
            )

        logger.info(
            "Question list completed in {duration_ms}ms for consultation {consultation_id} with {question_count} questions",
            duration_ms=duration_ms,
            consultation_id=str(consultation_pk),
            question_count=question_count,
        )

        return response

    def get_queryset(self):
        query_start = time()
        consultation_uuid = self.kwargs["consultation_pk"]

        queryset = models.Question.objects.filter(consultation_id=consultation_uuid)

        # Staff users can see all questions, non-staff users only see questions for assigned consultations
        if not self.request.user.is_staff:
            queryset = queryset.filter(consultation__users=self.request.user)

        # Select related consultation to avoid N+1 queries
        queryset = queryset.select_related("consultation")

        # Prefetch multi-choice answers with response counts
        queryset = queryset.prefetch_related(
            Prefetch(
                "multichoiceanswer_set",
                queryset=models.MultiChoiceAnswer.objects.annotate(
                    prefetched_response_count=Count("response")
                ),
            )
        )

        # Use denormalized fields instead of expensive JOINs with COUNT DISTINCT
        # The fields total_responses and reviewed_responses_count are updated
        # when responses are created or annotations are marked as reviewed
        queryset = queryset.only(
            "id",
            "number",
            "text",
            "has_free_text",
            "has_multiple_choice",
            "theme_status",
            "total_responses",
            "reviewed_responses_count",
            "consultation_id",  # Include FK field for select_related
        )

        final_queryset = queryset.order_by("number")

        query_duration = int((time() - query_start) * 1000)
        logger.info(
            "Question queryset built in {duration_ms}ms for consultation {consultation_id}",
            duration_ms=query_duration,
            consultation_id=str(consultation_uuid),
        )

        return final_queryset

    @action(
        detail=True,
        methods=["get"],
        url_path="theme-information",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def theme_information(self, request, pk=None, consultation_pk=None):
        """Get all theme information for a question"""
        start_time = time()

        # Get the question object with consultation in one query
        question = self.get_object()

        # Get all themes for this question
        themes = models.SelectedTheme.objects.filter(question=question).values(
            "id", "name", "description"
        )

        serializer = ThemeInformationSerializer(data={"themes": list(themes)})
        serializer.is_valid()

        duration_ms = int((time() - start_time) * 1000)
        logger.info(
            "Theme information completed in {duration_ms}ms for question {question_id} in consultation {consultation_id} with {theme_count} themes",
            duration_ms=duration_ms,
            question_id=str(pk),
            consultation_id=str(consultation_pk),
            theme_count=len(themes),
        )

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        url_path="show-next",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def show_next_response(self, request, pk=None, consultation_pk=None):
        """Get the next response that needs human review for this question"""
        question = self.get_object()

        # Check if this question has free text (only free text questions have themes)
        if not question.has_free_text:
            return Response(
                {
                    "next_response": None,
                    "has_free_text": False,
                    "message": "This question does not have free text responses.",
                }
            )

        # Get the next response that has not been human reviewed
        # Left join with annotation to find responses without annotations or not reviewed
        next_response = (
            models.Response.objects.filter(
                question=question,
                free_text__isnull=False,  # Only responses with free text
                free_text__gt="",  # Non-empty free text
            )
            .exclude(
                annotation__human_reviewed=True  # Exclude already reviewed
            )
            .order_by("?")
            .first()
        )

        if next_response:
            return Response(
                {
                    "next_response": {
                        "id": str(next_response.id),
                        "consultation_id": str(question.consultation.id),
                        "question_id": str(question.id),
                    },
                    "has_free_text": True,
                    "message": "Next response found.",
                }
            )

        return Response(
            {
                "next_response": None,
                "has_free_text": True,
                "message": "This question does not have free text responses",
            }
        )
