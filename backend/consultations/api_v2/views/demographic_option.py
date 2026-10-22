from typing import ClassVar

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultations.api_v2.permissions import CanSeeConsultationV2
from consultations.api_v2.serializers import (
    DemographicOptionMergeSerializer,
    DemographicOptionMutationSerializer,
)
from consultations.models import Consultation, DemographicOption
from consultations.services.demographics import (
    DemographicOptionError,
    merge_demographic_options,
)


class DemographicOptionViewSet(ModelViewSet):
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2]
    serializer_class = DemographicOptionMutationSerializer

    def get_consultation(self) -> Consultation:
        return get_object_or_404(Consultation, pk=self.kwargs["consultation_pk"])

    def get_queryset(self):
        return DemographicOption.objects.filter(
            consultation_id=self.kwargs["consultation_pk"]
        ).order_by("field_name", "field_value")

    def get_serializer_class(self):
        if self.action == "merge":
            return DemographicOptionMergeSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["consultation"] = self.get_consultation()
        return context

    def perform_create(self, serializer):
        serializer.save(consultation=self.get_consultation())

    @action(detail=False, methods=["post"])
    def merge(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            option = merge_demographic_options(
                self.get_consultation(),
                serializer.validated_data["demographic_options"],
                serializer.validated_data["new_value"],
            )
        except DemographicOptionError as error:
            raise serializers.ValidationError({"demographic_options": [str(error)]}) from error
        return Response(DemographicOptionMutationSerializer(option).data)
