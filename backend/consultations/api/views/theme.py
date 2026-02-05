from backend.consultations import models
from backend.consultations.api.permissions import (
    CanSeeConsultation,
)
from backend.consultations.api.serializers import CrossCuttingThemeSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet


class ThemeViewSet(ReadOnlyModelViewSet):
    serializer_class = CrossCuttingThemeSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]

        queryset = models.CrossCuttingTheme.objects.filter(consultation_id=consultation_uuid)

        # Staff users can see all themes, non-staff users only see themes for assigned consultations
        if not self.request.user.is_staff:
            queryset = queryset.filter(consultation__users=self.request.user)

        return queryset.order_by("-created_at")
