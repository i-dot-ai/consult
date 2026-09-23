from typing import ClassVar

from django.db.models import Q
from rest_framework import status
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations.api_v2.permissions import CanSeeConsultationV2
from consultations.api_v2.serializers import (
    ConsultationCreateSerializerV2,
    ConsultationSerializerV2,
)
from consultations.models import Consultation
from ingest.jobs import delete_consultation_job


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
        return queryset.filter(
            Q(users=self.request.user) | Q(created_by=self.request.user)
        ).distinct()

    def perform_destroy(self, instance):
        delete_consultation_job.delay(instance.id)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {
                "message": f"Deletion of consultation '{instance.title}' has been queued",
                "consultation_id": str(instance.id),
            },
            status=status.HTTP_202_ACCEPTED,
        )
