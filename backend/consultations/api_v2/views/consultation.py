from typing import ClassVar

from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations.api_v2.permissions import CanSeeConsultationV2
from consultations.api_v2.serializers import (
    ConsultationCreateSerializerV2,
    ConsultationSerializerV2,
)
from consultations.models import Consultation


class ConsultationViewSet(CreateModelMixin, ReadOnlyModelViewSet):
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2 | IsAdminUser]

    def get_serializer_class(self):
        if self.action == "create":
            return ConsultationCreateSerializerV2
        return ConsultationSerializerV2

    def perform_create(self, serializer):
        consultation = serializer.save(code="", created_by=self.request.user)
        consultation.users.add(self.request.user)

    def get_queryset(self):
        queryset = Consultation.objects.prefetch_related("users").order_by("-created_at")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(users=self.request.user)
