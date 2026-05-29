from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultations import models
from consultations.api.filters import get_filtered_responses
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

        # Per-question/option response counts are computed in bulk via grouped queries
        # (see _annotate_response_counts) rather than per-row correlated subqueries, so
        # the cost is independent of the number of questions in the list.
        return queryset.prefetch_related("multichoiceanswer_set").order_by("number")

    def _annotate_response_counts(self, questions):
        """Attach response-count annotations to a batch of questions in bulk.

        Replaces the previous correlated subqueries (one execution per question/option)
        with a fixed handful of GROUP BY queries. The resulting attribute names match
        exactly what ``QuestionSerializer`` reads, so the serialized output is unchanged.
        """
        question_ids = [question.id for question in questions]
        if not question_ids:
            return questions

        through = models.Response.chosen_options.through

        # Total responses per question (all responses, matching the previous semantics).
        total_responses = dict(
            models.Response.objects.filter(question_id__in=question_ids)
            .values_list("question_id")
            .annotate(c=Count("*"))
            .values_list("question_id", "c")
        )
        # Distinct responses that selected at least one multi-choice option, per question.
        multi_choice_respondents = dict(
            through.objects.filter(response__question_id__in=question_ids)
            .values_list("response__question_id")
            .annotate(c=Count("response_id", distinct=True))
            .values_list("response__question_id", "c")
        )
        # Response count per multi-choice option.
        option_counts = dict(
            through.objects.filter(multichoiceanswer__question_id__in=question_ids)
            .values_list("multichoiceanswer_id")
            .annotate(c=Count("*"))
            .values_list("multichoiceanswer_id", "c")
        )

        include = self.request.query_params.get("include", "")
        want_reviewed = "proportion_of_audited_answers" in include
        reviewed_responses = {}
        if want_reviewed:
            reviewed_responses = dict(
                models.Response.objects.filter(
                    question_id__in=question_ids,
                    free_text__isnull=False,
                    free_text__gt="",
                    annotation__human_reviewed=True,
                )
                .values_list("question_id")
                .annotate(c=Count("*"))
                .values_list("question_id", "c")
            )

        for question in questions:
            question.prefetched_total_responses = total_responses.get(question.id, 0)
            question.prefetched_multi_choice_respondent_count = multi_choice_respondents.get(
                question.id, 0
            )
            if want_reviewed:
                question.prefetched_reviewed_responses = reviewed_responses.get(question.id, 0)
            for option in question.multichoiceanswer_set.all():
                option.prefetched_response_count = option_counts.get(option.id, 0)

        return questions

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        questions = page if page is not None else list(queryset)
        self._annotate_response_counts(questions)
        serializer = self.get_serializer(questions, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        # Keep response counts populated on the serialized (PATCH) response, since
        # get_object() no longer carries them.
        self._annotate_response_counts([serializer.instance])

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single question with dynamically calculated multi-choice counts
        when filters are applied.
        """
        question = self.get_object()
        self._annotate_response_counts([question])

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

            # Get filtered responses
            filtered_responses = get_filtered_responses(
                request.query_params, consultation_pk, question_id=pk
            )

            # Recalculate multi-choice counts with filters
            multichoice_answers = models.MultiChoiceAnswer.objects.filter(
                question=question
            ).annotate(
                prefetched_response_count=Count(
                    "response",
                    filter=Q(response__in=filtered_responses),
                    distinct=True,
                )
            )

            # Replace the prefetched multichoice answers
            question._prefetched_objects_cache["multichoiceanswer_set"] = list(multichoice_answers)

            # Recalculate multi-choice respondent count with filters
            question.prefetched_multi_choice_respondent_count = (
                filtered_responses.filter(chosen_options__isnull=False).distinct().count()
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

        non_empty_filter = ~Q(
            responseannotation__response__free_text__in=models.EMPTY_FREE_TEXT_VALUES
        )

        if has_filters:
            filtered_responses = get_filtered_responses(
                request.query_params, consultation_pk, question_id=pk
            )
            themes = themes.annotate(
                count=Count(
                    "responseannotation",
                    filter=Q(responseannotation__response__in=filtered_responses)
                    & non_empty_filter,
                    distinct=True,
                )
            )
        else:
            themes = themes.annotate(
                count=Count("responseannotation", filter=non_empty_filter, distinct=True)
            )

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
