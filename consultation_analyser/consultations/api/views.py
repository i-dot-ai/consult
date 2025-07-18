from collections import defaultdict

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import models
from ..views.decorators import user_can_see_consultation, user_can_see_dashboards
from .serializers import DemographicOptionsSerializer


class DemographicOptionsAPIView(APIView):
    @user_can_see_dashboards
    @user_can_see_consultation
    def get(self, request, consultation_slug, question_slug):
        """Get all demographic options for a consultation"""
        consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
        
        # Get all demographic fields and their possible values from normalized storage
        options = (
            models.DemographicOption.objects.filter(consultation=consultation)
            .values_list("field_name", "field_value")
            .order_by("field_name", "field_value")
        )
        
        result = defaultdict(list)
        for field_name, field_value in options:
            result[field_name].append(field_value)
        
        serializer = DemographicOptionsSerializer(
            data={"demographic_options": dict(result)}
        )
        serializer.is_valid()
        
        return Response(serializer.data)