from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets

from consultation_analyser.api.serializers import (
    ConsultationSerializer,
    QuestionSerializer,
    ResponseSerializer,
)
from consultation_analyser.consultations.models import Consultation, Question, Response


class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer

    def get_queryset(self):
        return Consultation.objects.filter(users=self.request.user).order_by("-created_at")


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return Question.objects.filter(
            consultation__id=consultation_uuid, consultation__users=self.request.user
        ).order_by("-created_at")


class ResponseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ResponseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "annotation__sentiment",
        "annotation__themes",
        "annotation__evidence_rich",
        "free_text",
    ]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        question_uuid = self.kwargs["question_pk"]
        return (
            Response.objects.filter(
                question_id=question_uuid,
                question__consultation_id=consultation_uuid,
                question__consultation__users=self.request.user,
            )
            .select_related("annotation")
            .prefetch_related("annotation__themes")
            .order_by("-created_at")
        )
