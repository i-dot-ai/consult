from typing import ClassVar

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from consultations.api_v2.permissions import CanSeeConsultationV2
from consultations.api_v2.serializers import DemographicOptionMutationSerializer
from consultations.models import Consultation, DemographicOption


class DemographicOptionViewSet(ModelViewSet):
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2]
    serializer_class = DemographicOptionMutationSerializer

    def get_consultation(self) -> Consultation:
        return get_object_or_404(Consultation, pk=self.kwargs["consultation_pk"])

    def get_queryset(self):
        return DemographicOption.objects.filter(
            consultation_id=self.kwargs["consultation_pk"]
        ).order_by("field_name", "field_value")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["consultation"] = self.get_consultation()
        return context

    def perform_create(self, serializer):
        serializer.save(consultation=self.get_consultation())
