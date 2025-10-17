from rest_framework.viewsets import ReadOnlyModelViewSet

from consultation_analyser.consultations import models
from consultation_analyser.consultations.api.permissions import (
    CanSeeConsultation,
    HasDashboardAccess,
)
from consultation_analyser.consultations.api.serializers import CrossCuttingThemeSerializer


class ThemeViewSet(ReadOnlyModelViewSet):
    serializer_class = CrossCuttingThemeSerializer
    permission_classes = [HasDashboardAccess, CanSeeConsultation]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        return models.CrossCuttingTheme.objects.filter(
            consultation_id=consultation_uuid, consultation__users=self.request.user
        ).order_by("-created_at")
