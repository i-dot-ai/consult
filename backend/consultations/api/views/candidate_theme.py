from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.consultations import models
from backend.consultations.api.permissions import CanSeeConsultation
from backend.consultations.api.serializers import (
    CandidateThemeSerializer,
    SelectedThemeSerializer,
)


class CandidateThemeViewSet(ModelViewSet):
    serializer_class = CandidateThemeSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation]
    http_method_names = ["get", "post"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        question_uuid = self.kwargs["question_pk"]

        queryset = models.CandidateTheme.objects.filter(
            question__consultation_id=consultation_uuid,
            question_id=question_uuid,
        )

        # Staff users can see all candidate themes, non-staff users only see themes for assigned consultations
        if not self.request.user.is_staff:
            queryset = queryset.filter(question__consultation__users=self.request.user)

        return queryset.order_by("-approximate_frequency")

    def list(self, request, consultation_pk=None, question_pk=None):
        """List candidate themes for a question with nested children"""
        # Get all themes for this question to build the tree efficiently
        all_themes = list(self.get_queryset())
        
        # Build a lookup of children by parent_id
        children_by_parent = {}
        for theme in all_themes:
            parent_id = theme.parent_id
            if parent_id not in children_by_parent:
                children_by_parent[parent_id] = []
            children_by_parent[parent_id].append(theme)
        
        # Get root themes (no parent)
        roots = children_by_parent.get(None, [])
        
        # Pass children lookup to serializer context
        page = self.paginate_queryset(roots)
        serializer = CandidateThemeSerializer(
            page, 
            many=True, 
            context={'children_by_parent': children_by_parent}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path="select",
        permission_classes=[IsAuthenticated, CanSeeConsultation],
    )
    def select(self, request, consultation_pk=None, question_pk=None, pk=None):
        """Select a candidate theme to add as a selected theme"""
        candidate_theme = get_object_or_404(self.get_queryset(), pk=pk)

        if candidate_theme.selectedtheme:
            selected_theme = candidate_theme.selectedtheme
            serializer = SelectedThemeSerializer(selected_theme)
            return Response(serializer.data, status=200)

        selected_theme = models.SelectedTheme.objects.create(
            question=candidate_theme.question,
            name=candidate_theme.name,
            description=candidate_theme.description,
            last_modified_by=request.user,
        )

        candidate_theme.selectedtheme_id = selected_theme.id
        candidate_theme.save(update_fields=["selectedtheme_id"])

        serializer = SelectedThemeSerializer(selected_theme)
        return Response(serializer.data, status=201)
