from typing import ClassVar

from django.db.models import Count, Q
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations.api_v2.permissions import CanSeeConsultationV2
from consultations.api_v2.serializers import (
    DemographicResponseMergeSerializer,
    QuestionSetupSerializer,
)
from consultations.models import Question
from consultations.models import Response as ConsultationResponse
from consultations.services.setup_status import update_upload_status_for_questions


class QuestionViewSet(UpdateModelMixin, DestroyModelMixin, ReadOnlyModelViewSet):
    serializer_class = QuestionSetupSerializer
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2 | IsAdminUser]
    http_method_names: ClassVar[list] = ["get", "post", "patch", "delete"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "merge_demographics":
            return DemographicResponseMergeSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        return (
            Question.objects.filter(consultation_id=self.kwargs["consultation_pk"])
            .annotate(
                response_count=Count(
                    "response", filter=Q(response__text__isnull=False) & ~Q(response__text="")
                )
            )
            .order_by("number")
        )

    def perform_destroy(self, instance):
        consultation = instance.consultation
        instance.delete()
        update_upload_status_for_questions(consultation)

    @action(detail=True, methods=["post"], url_path="demographics/merge")
    def merge_demographics(self, request, *args, **kwargs):
        question = self.get_object()
        if question.type != Question.QuestionType.DEMOGRAPHIC:
            raise serializers.ValidationError(
                {"question": "Responses can only be merged for a demographic question."}
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
