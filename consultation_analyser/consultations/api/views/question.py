from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultation_analyser.consultations import models
from consultation_analyser.consultations.api.permissions import (
    CanSeeConsultation,
    HasDashboardAccess,
)
from consultation_analyser.consultations.api.serializers import (
    QuestionSerializer,
    ThemeInformationSerializer,
)


class QuestionViewSet(ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    filterset_fields = ["has_free_text"]
    http_method_names = ["get", "patch", "delete"]

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
