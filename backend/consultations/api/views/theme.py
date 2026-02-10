from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations import models
from consultations.api.permissions import (
    CanSeeConsultation,
)
from consultations.api.serializers import CrossCuttingThemeSerializer


class ThemeViewSet(ReadOnlyModelViewSet):
    serializer_class = CrossCuttingThemeSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation]
    http_method_names = ["get"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]

        queryset = models.CrossCuttingTheme.objects.filter(consultation_id=consultation_uuid)

        # Staff users can see all themes, non-staff users only see themes for assigned consultations
        if not self.request.user.is_staff:
            queryset = queryset.filter(consultation__users=self.request.user)

        return queryset.order_by("-created_at")
