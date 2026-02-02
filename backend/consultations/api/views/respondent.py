from backend.consultations import models
from backend.consultations.api.permissions import (
    CanSeeConsultation,
)
from backend.consultations.api.serializers import RespondentSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet


class RespondentViewSet(ModelViewSet):
    serializer_class = RespondentSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation]
    filterset_fields = {"themefinder_id": ["exact", "gte", "lte"]}
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        
        queryset = models.Respondent.objects.filter(consultation_id=consultation_uuid)
        
        # Staff users can see all respondents, non-staff users only see respondents for assigned consultations
        if not self.request.user.is_staff:
            queryset = queryset.filter(consultation__users=self.request.user)
            
        return queryset.order_by("-created_at")
