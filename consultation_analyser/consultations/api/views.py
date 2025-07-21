from collections import defaultdict

import orjson
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import models
from .permissions import CanSeeConsultation, HasDashboardAccess
from .serializers import (
    DemographicAggregationsSerializer,
    DemographicOptionsSerializer,
    FilterSerializer,
    QuestionInformationSerializer,
    ThemeAggregationsSerializer,
    ThemeInformationSerializer,
)
from .utils import (
    build_respondent_data_fast,
    build_response_filter_query,
    get_consultation_and_question,
    get_filtered_responses_with_themes,
    parse_filters_from_serializer,
)


class DemographicOptionsAPIView(APIView):
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    
    def get(self, request, consultation_slug, question_slug):
        """Get all demographic options for a consultation"""
        question = get_consultation_and_question(consultation_slug, question_slug)
        consultation = question.consultation
        
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
        question = get_consultation_and_question(consultation_slug, question_slug)
        
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


class ThemeInformationAPIView(APIView):
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    
    def get(self, request, consultation_slug, question_slug):
        """Get all theme information for a question"""
        # Get the question object with consultation in one query
        question = get_consultation_and_question(consultation_slug, question_slug)
        
        # Get all themes for this question
        themes = models.Theme.objects.filter(question=question).values("id", "name", "description")
        
        serializer = ThemeInformationSerializer(
            data={"themes": list(themes)}
        )
        serializer.is_valid()
        
        return Response(serializer.data)


class ThemeAggregationsAPIView(APIView):
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    
    def get(self, request, consultation_slug, question_slug):
        """Get theme aggregations for filtered responses"""
        from django.db.models import Count
        
        # Get the question object with consultation in one query
        question = get_consultation_and_question(consultation_slug, question_slug)
        
        # Validate query parameters
        filter_serializer = FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        
        # Parse filters
        filters = parse_filters_from_serializer(filter_serializer.validated_data)
        
        # Database-level aggregation using Django ORM hybrid approach
        theme_aggregations = {}
        
        if question.has_free_text:
            # Build base query with all filters applied
            response_filter = build_response_filter_query(filters, question)
            
            # Get theme counts directly from database with JOIN
            theme_counts = (
                models.Theme.objects.filter(
                    responseannotation__response__in=models.Response.objects.filter(response_filter)
                )
                .values("id")
                .annotate(count=Count("responseannotation__response"))
                .order_by("id")
            )
            
            theme_aggregations = {str(theme["id"]): theme["count"] for theme in theme_counts}
        
        serializer = ThemeAggregationsSerializer(
            data={"theme_aggregations": theme_aggregations}
        )
        serializer.is_valid()
        
        return Response(serializer.data)


class FilteredResponsesAPIView(APIView):
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    
    def get(self, request, consultation_slug, question_slug):
        """Get paginated filtered responses with orjson optimization"""
        from django.core.paginator import Paginator
        
        # Get the question object with consultation in one query
        question = get_consultation_and_question(consultation_slug, question_slug)
        
        # Validate query parameters
        filter_serializer = FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        
        # Parse filters
        filters = parse_filters_from_serializer(filter_serializer.validated_data)
        
        # Get pagination parameters from validated data
        page_num = filter_serializer.validated_data.get("page", 1)
        page_size = filter_serializer.validated_data.get("page_size", 50)
        
        # Get filtered responses with themes (optimized with prefetching)
        filtered_qs = get_filtered_responses_with_themes(question, filters)
        
        # Use Django's lazy pagination
        paginator = Paginator(filtered_qs, page_size, allow_empty_first_page=True)
        page_obj = paginator.page(page_num)
        
        # Get total respondents count for this question (single query)
        all_respondents_count = models.Response.objects.filter(question=question).count()
        
        # Use orjson for faster serialization of large response sets
        data = {
            "all_respondents": [build_respondent_data_fast(r) for r in page_obj.object_list],
            "has_more_pages": page_obj.has_next(),
            "respondents_total": all_respondents_count,
            "filtered_total": paginator.count,
        }
        
        # Return orjson-optimized HttpResponse
        return HttpResponse(
            orjson.dumps(data),
            content_type="application/json"
        )


class QuestionInformationAPIView(APIView):
    permission_classes = [HasDashboardAccess, CanSeeConsultation]
    
    def get(self, request, consultation_slug, question_slug):
        """Get basic question information"""
        # Get the question object with consultation in one query
        question = get_consultation_and_question(consultation_slug, question_slug)
        
        data = {
            "question_text": question.text,
            "total_responses": question.total_responses,
        }
        
        serializer = QuestionInformationSerializer(data=data)
        serializer.is_valid()
        
        return Response(serializer.data)