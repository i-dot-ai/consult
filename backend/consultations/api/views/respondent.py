from rest_framework.viewsets import ModelViewSet

from backend.consultations import models
from backend.consultations.api.permissions import (
    CanSeeConsultation,
    HasDashboardAccess,
)
from backend.consultations.api.serializers import RespondentSerializer


class RespondentViewSet(ModelViewSet):
    serializer_class = RespondentSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    filterset_fields = {"themefinder_id": ["exact", "gte", "lte"]}
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return models.Respondent.objects.filter(
            consultation_id=consultation_uuid, consultation__users=self.request.user
        ).order_by("-created_at")
