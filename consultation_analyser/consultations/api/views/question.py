from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultation_analyser.consultations import models
from consultation_analyser.consultations.api.permissions import CanSeeConsultation
from consultation_analyser.consultations.api.serializers import (
    QuestionSerializer,
    ThemeInformationSerializer, QuestionExportSerializer,
)
from consultation_analyser.consultations.export_user_theme import export_user_theme_job


class QuestionViewSet(ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [CanSeeConsultation]
    filterset_fields = ["has_free_text"]
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return (
            models.Question.objects.filter(
                consultation_id=consultation_uuid, consultation__users=self.request.user
            )
            .annotate(response_count=Count("response"))
            .order_by("number")
        )

    @action(detail=True, methods=["get"], url_path="theme-information")
    def theme_information(self, request, pk=None, consultation_pk=None):
        """Get all theme information for a question"""
        # Get the question object with consultation in one query
        question = self.get_object()

        # Get all themes for this question
        themes = models.SelectedTheme.objects.filter(question=question).values(
            "id", "name", "description"
        )

        serializer = ThemeInformationSerializer(data={"themes": list(themes)})
        serializer.is_valid()

        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="export")
    def export_user_theme(self, request, pk=None, consultation_pk=None):
        question = self.get_object()
        serializer = QuestionExportSerializer(data=request.data)
        if serializer.is_valid():
            export_user_theme_job(question_id=question.id, s3_key=serializer.validated_data["s3_key"])
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

