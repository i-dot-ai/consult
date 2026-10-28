import csv
from pathlib import Path
from typing import ClassVar
from zipfile import BadZipFile

from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Prefetch, Q
from openpyxl.utils.exceptions import InvalidFileException
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, UpdateModelMixin
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from consultations.api_v2.permissions import CanSeeConsultationV2, IsConsultationOwnerOrSuperuser
from consultations.api_v2.serializers import (
    ConsultationCreateSerializerV2,
    ConsultationDeepValidationSerializerV2,
    ConsultationFileUploadSerializerV2,
    ConsultationSerializer,
    ConsultationUpdateSerializerV2,
)
from consultations.models import Consultation, FileUpload
from ingest.consultation_file import read_consultation_file
from ingest.deep_validation import deep_validate_file
from ingest.jobs import add_consultation_job, delete_consultation_job

logger = settings.LOGGER


class ConsultationViewSet(
    CreateModelMixin, UpdateModelMixin, DestroyModelMixin, ReadOnlyModelViewSet
):
    permission_classes: ClassVar[list] = [IsAuthenticated, CanSeeConsultationV2 | IsAdminUser]
    http_method_names: ClassVar[list] = ["get", "post", "patch", "delete"]
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
        if self.action == "deep_validation":
            return ConsultationDeepValidationSerializerV2
        if self.action == "partial_update":
            return ConsultationUpdateSerializerV2
        return ConsultationSerializer

    def perform_create(self, serializer):
        consultation = serializer.save(code="", created_by=self.request.user)
        consultation.users.add(self.request.user)

    def get_queryset(self):
        queryset = (
            Consultation.objects.select_related("created_by")
            .prefetch_related(
                "users",
                Prefetch("fileupload_set", queryset=FileUpload.objects.order_by("created_at")),
            )
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
    def deep_validation(self, request, *args, **kwargs):
        consultation = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data["file"]

        return Response(
            deep_validate_file(uploaded_file.read(), uploaded_file.name, consultation.data_source)
        )

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def upload(self, request, *args, **kwargs):
        consultation = self.get_object()
        if FileUpload.objects.filter(consultation=consultation).exists():
            raise serializers.ValidationError(
                {"file": "A file has already been uploaded for this consultation."}
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        try:
            read_consultation_file(uploaded_file, uploaded_file.name)
        except (
            csv.Error,
            InvalidFileException,
            UnicodeDecodeError,
            ValueError,
            BadZipFile,
        ) as error:
            logger.exception(
                "Error uploading file {file_name}",
                file_name=uploaded_file.name,
            )
            raise serializers.ValidationError({"file": str(error)}) from error

        file_upload = FileUpload(consultation=consultation, uploaded_by=request.user)
        extension = Path(uploaded_file.name).suffix.lower()
        requested_key = f"consultations/uploads/{consultation.id}/{file_upload.id}{extension}"
        file_upload.s3_key = default_storage.save(requested_key, uploaded_file)
        file_upload.save()
        consultation.survey_import_status = Consultation.SurveyImportStatus.FILE_UPLOADING
        consultation.save(update_fields=["survey_import_status"])
        try:
            add_consultation_job.delay(file_upload.id)
        except Exception as error:
            file_upload.status = FileUpload.Status.FAILED
            file_upload.error_message = str(error)
            file_upload.save(update_fields=["status", "error_message"])
            consultation.survey_import_status = Consultation.SurveyImportStatus.IMPORT_FAILED
            consultation.save(update_fields=["survey_import_status"])
            raise

        return Response(
            {
                "id": str(file_upload.id),
                "s3_key": file_upload.s3_key,
                "status": file_upload.status,
                "survey_import_status": consultation.survey_import_status,
            },
            status=status.HTTP_202_ACCEPTED,
        )
