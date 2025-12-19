from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultation_analyser.consultations import models
from consultation_analyser.consultations.api.permissions import CanSeeConsultation
from consultation_analyser.consultations.api.serializers import (
    QuestionSerializer,
    ThemeInformationSerializer,
)


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

    @action(detail=True, methods=["get"], url_path="test-debug")
    def test_debug(self, request, pk=None, consultation_pk=None):
        """Debug endpoint to test if actions work"""
        return Response({"status": "debug endpoint works"})

    @action(detail=True, methods=["get"], url_path="show-next")
    def show_next_response(self, request, pk=None, consultation_pk=None):
        """Get the next response that needs human review for this question"""
        question = self.get_object()

        # Check if this question has free text (only free text questions have themes)
        if not question.has_free_text:
            return Response({
                "next_response": None,
                "has_free_text": False,
                "message": "This question does not have free text responses."
            })

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
            return Response({
                "next_response": {
                    "id": str(next_response.id),
                    "consultation_id": str(question.consultation.id),
                    "question_id": str(question.id),
                },
                "has_free_text": True,
                "message": "Next response found."
            })

        return Response({
            "next_response": None,
            "has_free_text": True,
            "message": "No more responses to review."
        })
