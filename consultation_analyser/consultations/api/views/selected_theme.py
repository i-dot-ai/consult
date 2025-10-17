from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.viewsets import ModelViewSet

from consultation_analyser.consultations import models
from consultation_analyser.consultations.api.exceptions import (
    PreconditionFailed,
    PreconditionRequired,
)
from consultation_analyser.consultations.api.permissions import CanSeeConsultation
from consultation_analyser.consultations.api.serializers import SelectedThemeSerializer


class SelectedThemeViewSet(ModelViewSet):
    serializer_class = SelectedThemeSerializer
    permission_classes = [CanSeeConsultation]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        consultation_uuid = self.kwargs["consultation_pk"]
        question_uuid = self.kwargs["question_pk"]
        return models.SelectedTheme.objects.filter(
            question__consultation_id=consultation_uuid,
            question_id=question_uuid,
            question__consultation__users=self.request.user,
        )

    def perform_create(self, serializer):
        question = get_object_or_404(
            models.Question,
            pk=self.kwargs["question_pk"],
            consultation__users=self.request.user,
        )
        serializer.save(question=question, last_modified_by=self.request.user)

    def _parse_if_match_version(self, request):
        version = request.headers.get("If-Match")
        if not version:
            raise PreconditionRequired()

        try:
            return int(version.strip())
        except (TypeError, ValueError):
            raise ParseError(detail="Invalid If-Match header; expected integer version")

    def perform_update(self, serializer):
        expected_version = self._parse_if_match_version(self.request)

        with transaction.atomic():
            # Lock the selected theme to prevent concurrent updates
            qs = self.get_queryset().filter(pk=serializer.instance.pk).select_for_update()
            instance = qs.get()

            if instance.version != expected_version:
                raise PreconditionFailed(
                    detail={"message": "Version mismatch", "latest_version": instance.version}
                )

            serializer.instance = instance
            serializer.save(last_modified_by=self.request.user)

            # Bump version while lock held
            serializer.instance.version = instance.version + 1
            serializer.instance.save(update_fields=["version"])

            serializer.instance.refresh_from_db()

    def perform_destroy(self, instance):
        expected_version = self._parse_if_match_version(self.request)

        deleted_count, _ = (
            self.get_queryset().filter(pk=instance.pk, version=expected_version).delete()
        )

        if deleted_count == 0:
            # If no rows were deleted, the resource may either have a
            # different version or no longer exist.
            try:
                selected_theme = self.get_queryset().get(pk=instance.pk)
            except models.SelectedTheme.DoesNotExist:
                raise NotFound()

            raise PreconditionFailed(
                detail={"message": "Version mismatch", "latest_version": selected_theme.version}
            )
