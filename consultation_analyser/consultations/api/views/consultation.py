from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultation_analyser.consultations import models
from consultation_analyser.consultations.api.serializers import (
    ConsultationSerializer,
    DemographicOptionSerializer,
)


class ConsultationViewSet(ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["code"]
    http_method_names = ["get", "patch"]

    def get_queryset(self):
        return models.Consultation.objects.filter(users=self.request.user).order_by("-created_at")

    def get_object(self):
        consultation = get_object_or_404(models.Consultation, **self.kwargs)

        if not consultation.users.filter(pk=self.request.user.pk).exists():
            raise PermissionDenied("You don't have permission to access this object.")

        return consultation

    # permission_classes=[CanSeeConsultation]
    @action(
        detail=True,
        methods=["get"],
        url_path="demographic-options",
    )
    def demographic_options(self, request, pk=None):
        self.get_object()

        if not request.user.has_dashboard_access:
            raise PermissionDenied()

        data = (
            (
                models.DemographicOption.objects.filter(consultation_id=pk).annotate(
                    count=Count("respondent")
                )
            )
            .values("id", "field_name", "field_value", "count")
            .order_by("field_name", "field_value")
        )

        serializer = DemographicOptionSerializer(instance=data, many=True)

        return Response(serializer.data)
