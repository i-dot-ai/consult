from django.db.models import Case, Count, IntegerField, OuterRef, Prefetch, Q, Subquery, Value, When
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultations import models
from consultations.api.filters import get_filtered_response_ids, get_filtered_responses
from consultations.api.permissions import (
    CanSeeConsultation,
)
from consultations.api.serializers import (
    QuestionSerializer,
    QuestionThemeSerializer,
)


class QuestionPagination(PageNumberPagination):
    page_size = 500


class QuestionViewSet(ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation]
    filterset_fields = ["has_free_text"]
    http_method_names = ["get", "patch", "delete"]
    pagination_class = QuestionPagination

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]

        queryset = models.Question.objects.filter(consultation_id=consultation_uuid)

        # Staff users can see all questions, non-staff users only see questions for assigned consultations
        if not self.request.user.is_staff:
            queryset = queryset.filter(consultation__users=self.request.user)

        # Total responses per question (correlated subquery to avoid full-table JOIN)
        question_response_count = Subquery(
            models.Response.objects.filter(question_id=OuterRef("pk"))
            .order_by()
            .values("question_id")
            .annotate(c=Count("*"))
            .values("c")
        )
        queryset = queryset.annotate(
            prefetched_total_responses=Coalesce(question_response_count, Value(0)),
        )

        # Response count per multi-choice answer (correlated subquery to avoid full-table JOIN)
        multichoice_response_count = Subquery(
            models.Response.chosen_options.through.objects.filter(
                multichoiceanswer_id=OuterRef("pk")
            )
            .order_by()
            .values("multichoiceanswer_id")
            .annotate(c=Count("*"))
            .values("c")
        )
        queryset = queryset.prefetch_related(
            Prefetch(
                "multichoiceanswer_set",
                queryset=models.MultiChoiceAnswer.objects.annotate(
                    prefetched_response_count=Coalesce(multichoice_response_count, Value(0))
                ),
            )
        )

        # Reviewed responses per question (only when explicitly requested)
        if "proportion_of_audited_answers" in self.request.query_params.get("include", ""):
            reviewed_response_count = Subquery(
                models.Response.objects.filter(
                    question_id=OuterRef("pk"),
                    free_text__isnull=False,
                    free_text__gt="",
                    annotation__human_reviewed=True,
                )
                .order_by()
                .values("question_id")
                .annotate(c=Count("*"))
                .values("c")
            )
            queryset = queryset.annotate(
                prefetched_reviewed_responses=Coalesce(reviewed_response_count, Value(0)),
            )

        return queryset.order_by("number")

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single question with dynamically calculated multi-choice counts
        when filters are applied.
        """
        question = self.get_object()

        # Check if any filters are applied
        filter_params = [
            "themeFilters",
            "demographics",
            "evidenceRich",
            "unseenResponsesOnly",
            "is_flagged",
            "multiple_choice_answer",
        ]
        has_filters = any(request.query_params.get(p) for p in filter_params)

        # Recalculate multi-choice counts with filters if needed
        if has_filters and question.has_multiple_choice:
            consultation_pk = self.kwargs["consultation_pk"]
            pk = kwargs["pk"]

            filtered_response_ids = get_filtered_response_ids(
                request.query_params, consultation_pk, question_id=pk, request=request
            )

            multichoice_answers = models.MultiChoiceAnswer.objects.filter(
                question=question
            ).annotate(
                prefetched_response_count=Count(
                    Case(
                        When(response__id__in=filtered_response_ids, then=1),
                        output_field=IntegerField(),
                    ),
                    distinct=True,
                )
            )

            # Replace the prefetched multichoice answers
            question._prefetched_objects_cache["multichoiceanswer_set"] = list(
                multichoice_answers
            )

        serializer = self.get_serializer(question)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        url_path="themes",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def themes(self, request, pk=None, consultation_pk=None):
        """Get themes for a question with response counts."""
        question = self.get_object()

        themes = models.SelectedTheme.objects.filter(question=question)

        filter_params = [
            "themeFilters",
            "demographics",
            "evidenceRich",
            "unseenResponsesOnly",
            "is_flagged",
            "multiple_choice_answer",
        ]
        has_filters = any(request.query_params.get(p) for p in filter_params)

        if has_filters:
            filtered_response_ids = get_filtered_response_ids(
                request.query_params, consultation_pk, question_id=pk, request=request
            )
            themes = themes.annotate(
                count=Count(
                    Case(
                        When(responseannotation__response_id__in=filtered_response_ids, then=1),
                        output_field=IntegerField(),
                    ),
                    distinct=True,
                )
            )
        else:
            themes = themes.annotate(count=Count("responseannotation", distinct=True))

        serializer = QuestionThemeSerializer(themes, many=True)
        return Response({"themes": serializer.data})

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
