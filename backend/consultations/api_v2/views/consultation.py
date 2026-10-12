import csv
from pathlib import Path
from typing import ClassVar
from zipfile import BadZipFile

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q
from openpyxl.utils.exceptions import InvalidFileException
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations.api_v2.permissions import CanSeeConsultationV2, IsConsultationOwnerOrSuperuser
from consultations.api_v2.serializers import (
    ConsultationCreateSerializerV2,
    ConsultationFileUploadSerializerV2,
    ConsultationSerializer,
)
from consultations.models import Consultation, FileUpload
from ingest.consultation_file import import_consultation_data, read_consultation_file
from ingest.jobs import delete_consultation_job

logger = settings.LOGGER


class ConsultationViewSet(CreateModelMixin, DestroyModelMixin, ReadOnlyModelViewSet):
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2 | IsAdminUser]
    filterset_fields: ClassVar[dict] = {"title": ["iexact"]}

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAuthenticated(), IsConsultationOwnerOrSuperuser()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return ConsultationCreateSerializerV2
        if self.action == "upload":
            return ConsultationFileUploadSerializerV2
        return ConsultationSerializer

    def perform_create(self, serializer):
        consultation = serializer.save(code="", created_by=self.request.user)
        consultation.users.add(self.request.user)

    def get_queryset(self):
        queryset = (
            Consultation.objects.select_related("created_by")
            .prefetch_related("users")
            .order_by("-created_at")
        )
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

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def upload(self, request, *args, **kwargs):
        consultation = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        try:
            question_texts, response_rows = read_consultation_file(
                uploaded_file, uploaded_file.name
            )
        except (
            csv.Error,
            InvalidFileException,
            UnicodeDecodeError,
            ValueError,
            BadZipFile,
        ) as error:
            raise serializers.ValidationError({"file": str(error)}) from error

        file_upload = FileUpload(consultation=consultation, uploaded_by=request.user)
        extension = Path(uploaded_file.name).suffix.lower()
        requested_key = f"consultations/uploads/{consultation.id}/{file_upload.id}{extension}"
        file_upload.s3_key = default_storage.save(requested_key, uploaded_file)
        try:
            with transaction.atomic():
                file_upload.save()
                question_count, response_count = import_consultation_data(
                    consultation, question_texts, response_rows
                )
        except Exception:
            try:
                default_storage.delete(file_upload.s3_key)
            except Exception:  # noqa: BLE001 - cleanup must not mask the import error
                logger.warning(
                    "Failed to clean up uploaded file {s3_key}",
                    s3_key=file_upload.s3_key,
                )
            raise

        return Response(
            {
                "id": str(file_upload.id),
                "s3_key": file_upload.s3_key,
                "question_count": question_count,
                "response_count": response_count,
            },
            status=status.HTTP_201_CREATED,
        )
