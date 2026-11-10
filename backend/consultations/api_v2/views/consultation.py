import csv
from pathlib import Path
from typing import ClassVar
from zipfile import BadZipFile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from openpyxl.utils.exceptions import InvalidFileException
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, UpdateModelMixin
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from authentication.models import User
from consultations.api_v2.permissions import (
    CanSeeConsultationV2,
    IsConsultationOwnerOrSuperuser,
)
from consultations.api_v2.serializers import (
    ConsultationCreateSerializerV2,
    ConsultationDeepValidationSerializerV2,
    ConsultationFileUploadSerializerV2,
    ConsultationSerializer,
    ConsultationUpdateSerializerV2,
    ConsultationUserAssignmentSerializerV2,
)
from consultations.models import Consultation, FileUpload
from data_pipeline import batch
from data_pipeline.sync.consultation_inputs import (
    assign_consultation_code,
    export_consultation_inputs_to_s3,
    sync_has_free_text_with_type,
)
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
        if self.action in ("assign_users", "remove_user", "destroy"):
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
        if self.action == "assign_users":
            return ConsultationUserAssignmentSerializerV2
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

    @action(detail=True, methods=["post"], url_path="assign-users", url_name="assign-users")
    def assign_users(self, request, *args, **kwargs):
        consultation = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        emails = serializer.validated_data["emails"]

        users = list(User.objects.filter(email__in=emails))
        existing_emails = {user.email for user in users}
        created_users = []
        for email in emails:
            if email in existing_emails:
                continue
            try:
                created_users.append(User.objects.create_user(email))
            except ValidationError:
                # Another request created this account between the lookup and now;
                # it is still new from this request's point of view.
                created_users.append(User.objects.get(email=email))

        consultation.users.add(*users, *created_users)
        logger.info(
            "Added {added_emails} to consultation {consultation_id} by {actor}, "
            "creating accounts for {created_emails}",
            added_emails=[user.email for user in [*users, *created_users]],
            created_emails=[user.email for user in created_users],
            consultation_id=str(consultation.id),
            actor=request.user.email,
        )
        return Response(
            {"added_count": len(users) + len(created_users)}, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["delete"], url_path="users", url_name="remove-user")
    def remove_user(self, request, *args, **kwargs):
        consultation = self.get_object()
        user_id = request.query_params.get("user_id", "")
        if not user_id.isdecimal():
            raise serializers.ValidationError(
                {"user_id": "Give the id of the person to remove as ?user_id=<id>."}
            )
        user = get_object_or_404(consultation.users, pk=int(user_id))
        if user == consultation.created_by:
            raise serializers.ValidationError(
                {"user": "The person who created the consultation cannot be removed."}
            )

        consultation.users.remove(user)
        logger.info(
            "Removed {removed_email} from consultation {consultation_id} by {actor}",
            removed_email=user.email,
            consultation_id=str(consultation.id),
            actor=request.user.email,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

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
            read_consultation_file(uploaded_file, uploaded_file.name, consultation.data_source)
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

    @action(
        detail=True,
        methods=["post"],
        url_path="find-themes",
        permission_classes=[IsAuthenticated, CanSeeConsultationV2],
    )
    def find_themes(self, request, pk=None) -> Response:
        """
        Submit AWS batch job to find themes for each free-text question.

        The found themes are automatically saved to the database as candidate
        themes when the job completes.
        (See: lambda/import_candidate_themes/import_candidate_themes_handler.py)

        Before submitting, derives has_free_text from question type, renders
        the ThemeFinder inputs layout to S3 from the database (the mirror of
        what scripts/setup_consultation.py used to upload), assigning a
        consultation code first if the consultation doesn't have one yet.

        Advances consultation to FINDING_THEMES stage

        URL: /api/consultations/{consultation_id}/find-themes/
        """
        try:
            consultation = self.get_object()
            logger.set_context_field("consultation_id", str(consultation.id))

            if consultation.stage != Consultation.Stage.SETUP:
                return Response(
                    {
                        "error": f"Consultation '{consultation.code}' not in setup stage",
                        "detail": "ThemeFinder can only process consultations in the setup stage",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Derive has_free_text from the question type at kickoff so the
            # guard, the mirror and the pipeline all ask one consistent
            # question, regardless of what the setup flow left behind.
            synced_flags = sync_has_free_text_with_type(consultation)
            if synced_flags:
                logger.info(
                    "Synced has_free_text from question type for {synced_flags} "
                    "questions of consultation '{consultation_title}'",
                    synced_flags=synced_flags,
                    consultation_title=consultation.title,
                )

            free_text_questions = consultation.question_set.filter(has_free_text=True)
            if not free_text_questions.exists():
                return Response(
                    {
                        "error": f"Consultation '{consultation.code}' has no free-text questions",
                        "detail": "ThemeFinder can only process consultations with free-text responses",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # The mirror runs inline on purpose: the Batch job must not start
            # before the S3 inputs exist. Deliberately synchronous rather than
            # an RQ job — pushes were historically <60s even at full scale
            # (see export_consultation_inputs_to_s3).
            consultation_code = assign_consultation_code(consultation)
            question_parts = export_consultation_inputs_to_s3(consultation, consultation_code)
            logger.info(
                "Mirrored {question_parts} question parts to s3 for consultation "
                "'{consultation_code}' before find-themes kickoff",
                question_parts=question_parts,
                consultation_code=consultation_code,
            )

            batch.submit_job(
                job_type="FIND_THEMES",
                consultation_code=consultation_code,
                consultation_name=consultation.title,
                user_id=request.user.id,
                model_name=consultation.model_name,
            )

            logger.info(
                "Find Themes job submitted for consultation {consultation_title} by user {user_id}",
                consultation_title=consultation.title,
                user_id=request.user.id,
            )

            try:
                consultation.stage = Consultation.Stage.FINDING_THEMES
                consultation.save(update_fields=["stage"])
            except Exception:
                logger.exception(
                    "Failed to update consultation stage for consultation "
                    "{consultation_title} while starting Find Themes job",
                    consultation_title=consultation.title,
                )

            return Response(
                {
                    "message": f"Find Themes job started for consultation '{consultation.title}'",
                    "consultation_id": consultation.id,
                    "consultation_code": consultation_code,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except Exception as e:
            logger.exception(
                "Error starting Find Themes job for consultation {consultation_title}",
                consultation_title=consultation.title,
            )
            return Response(
                {
                    "error": "Failed to start Find Themes job",
                    "detail": str(e) if settings.DEBUG else "An unexpected error occurred",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
