from typing import ClassVar

from django.db.models import Count, Q
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations.api_v2.permissions import CanSeeConsultationV2
from consultations.api_v2.serializers import QuestionSetupSerializer
from consultations.models import Question


class QuestionViewSet(UpdateModelMixin, DestroyModelMixin, ReadOnlyModelViewSet):
    serializer_class = QuestionSetupSerializer
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2 | IsAdminUser]
    http_method_names: ClassVar[list] = ["get", "patch", "delete"]
    pagination_class = None

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
