from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultation_analyser.consultations.api.permissions import (
    CanSeeConsultation,
    HasDashboardAccess,
)
from consultation_analyser.consultations.api.serializers import (
    ConsultationSerializer,
    DemographicOptionSerializer,
)
from consultation_analyser.consultations.models import Consultation, DemographicOption


class ConsultationViewSet(ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation | IsAdminUser]
    filterset_fields = ["slug"]
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Consultation.objects.all().order_by("-created_at")
        return Consultation.objects.filter(users=self.request.user).order_by("-created_at")

    @action(
        detail=False, methods=["get"], url_path="assigned", permission_classes=[IsAuthenticated]
    )
    def assigned(self, request, *args, **kwargs):
        """Return consultations the current user is a member of."""
        qs = Consultation.objects.filter(users=request.user).order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        url_path="demographic-options",
        permission_classes=[HasDashboardAccess],
    )
    def demographic_options(self, request, pk=None):
        self.get_object()

        data = (
            (
                DemographicOption.objects.filter(consultation_id=pk).annotate(
                    count=Count("respondent")
                )
            )
            .values("id", "field_name", "field_value", "count")
            .order_by("field_name", "field_value")
        )

        serializer = DemographicOptionSerializer(instance=data, many=True)

        return Response(serializer.data)
