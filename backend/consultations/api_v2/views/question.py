from typing import ClassVar

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations.api_v2.filters import get_filtered_response_ids
from consultations.api_v2.permissions import CanSeeConsultationV2
from consultations.api_v2.serializers import (
    DemographicAnswerSerializer,
    DemographicResponseMergeSerializer,
    QuestionDashboardSerializerV2,
    QuestionSetupSerializer,
)
from consultations.models import MultiChoiceAnswer, Question
from consultations.models import Response as ConsultationResponse
from consultations.services.setup_status import update_survey_import_status_for_questions

SAMPLE_ANSWER_COUNT = 3

# Query params that trigger filtered count recalculation on the dashboard question page
DASHBOARD_FILTER_PARAMS = (
    "themeFilters",
    "demographics",
    "evidenceRich",
    "unseenResponsesOnly",
    "is_flagged",
    "multiple_choice_answer",
    "searchValue",
)


class QuestionViewSet(UpdateModelMixin, DestroyModelMixin, ReadOnlyModelViewSet):
    serializer_class = QuestionSetupSerializer
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2 | IsAdminUser]
    http_method_names: ClassVar[list] = ["get", "post", "patch", "delete"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "demographics":
            return DemographicAnswerSerializer
        if self.action == "merge_demographics":
            return DemographicResponseMergeSerializer
        if self.action in ("retrieve", "list"):
            # v2 dashboard question payloads carry the response counts and
            # multi-choice answers; the write actions keep the setup shape.
            return QuestionDashboardSerializerV2
        return super().get_serializer_class()

    def get_queryset(self):
        queryset = (
            Question.objects.filter(consultation_id=self.kwargs["consultation_pk"])
            .prefetch_related("multichoiceanswer_set")
            .annotate(
                response_count=Count(
                    "response", filter=Q(response__text__isnull=False) & ~Q(response__text="")
                )
            )
            .order_by("number")
        )
        if self.action == "retrieve":
            # The dashboard question page surfaces the proportion of audited
            # answers; annotate the reviewed count for the single object.
            reviewed_response_count = Subquery(
                ConsultationResponse.objects.filter(
                    question_id=OuterRef("pk"), annotation__human_reviewed=True
                )
                .order_by()
                .values("question_id")
                .annotate(c=Count("*"))
                .values("c")
            )
            queryset = queryset.annotate(
                prefetched_reviewed_responses=Coalesce(reviewed_response_count, Value(0))
            )
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a question with counts recalculated when dashboard filters apply.

        Mirrors the v1 question page: unfiltered reads serve the denormalised
        counts; filtered reads recalculate them in memory for the current
        response subset.
        """
        question = self.get_object()

        if any(request.query_params.get(param) for param in DASHBOARD_FILTER_PARAMS):
            consultation_pk = self.kwargs["consultation_pk"]
            filtered_ids = get_filtered_response_ids(
                request.query_params, consultation_pk, question_id=question.pk
            )
            filtered_responses = ConsultationResponse.objects.filter(id__in=filtered_ids)
            question.calculate_response_counts(filtered_responses)

            multichoice_answers = MultiChoiceAnswer.objects.filter(question=question).annotate(
                prefetched_response_count=Count(
                    "response", filter=Q(response__id__in=filtered_ids), distinct=True
                )
            )
            question._prefetched_objects_cache = {
                **getattr(question, "_prefetched_objects_cache", {}),
                "multichoiceanswer_set": list(multichoice_answers),
            }

        serializer = self.get_serializer(question)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        consultation = instance.consultation
        instance.delete()
        update_survey_import_status_for_questions(consultation)

    @action(detail=True, methods=["get"], url_path="sample-answers")
    def sample_answers(self, request, *args, **kwargs):
        question = self.get_object()
        answers = ConsultationResponse.objects.filter(question=question).exclude(
            Q(text__isnull=True) | Q(text="")
        )
        return Response(
            {
                "answers": list(
                    answers.order_by("id").values_list("text", flat=True)[:SAMPLE_ANSWER_COUNT]
                ),
                "total_count": question.response_count,
            }
        )

    @action(detail=True, methods=["get"], url_path="demographics")
    def demographics(self, request, *args, **kwargs):
        question = self.get_object()
        if not question.is_chartable:
            raise serializers.ValidationError(
                {"question": "Answers can only be listed for a closed or demographic question."}
            )

        answers = (
            ConsultationResponse.objects.filter(question=question)
            .exclude(Q(text__isnull=True) | Q(text=""))
            .values("text")
            .annotate(count=Count("id"), responses=ArrayAgg("id", ordering="id"))
            .order_by("-count", "text")
        )
        return Response(self.get_serializer(answers, many=True).data)

    @action(detail=True, methods=["post"], url_path="demographics/merge")
    def merge_demographics(self, request, *args, **kwargs):
        question = self.get_object()
        if not question.is_chartable:
            raise serializers.ValidationError(
                {"question": "Responses can only be merged for a closed or demographic question."}
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response_ids = serializer.validated_data["responses"]
        responses = ConsultationResponse.objects.filter(question=question, id__in=response_ids)
        if responses.count() != len(response_ids):
            raise serializers.ValidationError(
                {"responses": "All responses must exist and belong to this question."}
            )

        responses.update(text=serializer.validated_data["new_value"])
        return Response(serializer.data)
