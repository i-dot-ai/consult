from collections import defaultdict

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import models
from .permissions import CanSeeConsultation, HasDashboardAccess
from .serializers import (
    DemographicAggregationsSerializer,
    DemographicOptionsSerializer,
    FilterSerializer,
)
from .utils import build_response_filter_query, parse_filters_from_serializer


class DemographicOptionsAPIView(APIView):
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    
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


class DemographicAggregationsAPIView(APIView):
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    
    def get(self, request, consultation_slug, question_slug):
        """Get demographic aggregations for filtered responses"""
        # Get the question object with consultation in one query
        question = get_object_or_404(
            models.Question.objects.select_related("consultation"),
            slug=question_slug,
            consultation__slug=consultation_slug,
        )
        
        # Validate query parameters
        filter_serializer = FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        
        # Parse filters
        filters = parse_filters_from_serializer(filter_serializer.validated_data)
        
        # Single query that joins responses -> respondents and gets demographics directly
        response_filter = build_response_filter_query(filters, question)
        respondents_data = models.Respondent.objects.filter(
            response__in=models.Response.objects.filter(response_filter)
        ).values_list("demographics", flat=True)
        
        # Aggregate in memory (much faster than nested loops)
        aggregations = defaultdict(lambda: defaultdict(int))
        for demographics in respondents_data:
            if demographics:
                for field_name, field_value in demographics.items():
                    value_str = str(field_value)
                    aggregations[field_name][value_str] += 1
        
        result = {field: dict(counts) for field, counts in aggregations.items()}
        
        serializer = DemographicAggregationsSerializer(
            data={"demographic_aggregations": result}
        )
        serializer.is_valid()
        
        return Response(serializer.data)