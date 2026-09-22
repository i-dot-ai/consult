from typing import ClassVar

from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations.models import Consultation

from .permissions import CanSeeConsultationV2
from .serializers import ConsultationSerializerV2


class ConsultationViewSet(ReadOnlyModelViewSet):
    serializer_class = ConsultationSerializerV2
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2 | IsAdminUser]

    def get_queryset(self):
        queryset = Consultation.objects.prefetch_related("users").order_by("-created_at")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(users=self.request.user)
