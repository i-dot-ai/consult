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
from consultation_analyser.support_console import ingest
from consultation_analyser.support_console.views.consultations import delete_consultation_job


class ConsultationViewSet(ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation | IsAdminUser]
    filterset_fields = ["code"]
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        scope = self.request.query_params.get("scope")
        if scope == "assigned":
            return Consultation.objects.filter(users=self.request.user).order_by("-created_at")
        elif self.request.user.is_staff:
            return Consultation.objects.all().order_by("-created_at")
        return Consultation.objects.filter(users=self.request.user).order_by("-created_at")

    def perform_destroy(self, instance):
        delete_consultation_job(instance)

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

    @action(
        detail=False,
        methods=["get"],
        url_path="consultation-folders",
        permission_classes=[HasDashboardAccess],
    )
    def consultation_folders(self, request):
        consultation_folders = ingest.get_consultation_codes()

        serializer = ConsultationSerializer(instance=consultation_folders, many=True)

        return Response(serializer.data)
