from typing import Any
from uuid import UUID

import backend.data_pipeline.batch as batch
import backend.data_pipeline.s3 as s3
import sentry_sdk
from backend.authentication.models import User
from backend.consultations.api.permissions import (
    CanSeeConsultation,
)
from backend.consultations.api.serializers import (
    ConsultationExportSerializer,
    ConsultationFolderQuerySerializer,
    ConsultationSerializer,
    ConsultationSetupSerializer,
    DemographicOptionSerializer,
)
from backend.consultations.export_user_theme import export_user_theme_job
from backend.consultations.models import (
    Consultation,
    DemographicOption,
    SelectedTheme,
)
from backend.data_pipeline import jobs
from backend.data_pipeline.sync.selected_themes import export_selected_themes_to_s3
from backend.ingest.jobs import (
    delete_consultation_job,
)
from django.conf import settings
from django.db.models import Count
from django.http import Http404
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

logger = settings.LOGGER


class ConsultationViewSet(ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation | IsAdminUser]
    filterset_fields = ["code"]
    http_method_names = ["get", "patch", "delete", "post"]

    def get_queryset(self):
        scope = self.request.query_params.get("scope")
        if scope == "assigned":
            return Consultation.objects.filter(users=self.request.user).prefetch_related("users").order_by("-created_at")
        elif self.request.user.is_staff:
            return Consultation.objects.all().prefetch_related("users").order_by("-created_at")
        return Consultation.objects.filter(users=self.request.user).prefetch_related("users").order_by("-created_at")

    def get_permissions(self):
        """
        Override permissions for specific actions
        """
        permission_classes = self.permission_classes

        if self.action == "destroy":
            # Only admin users can delete consultations
            permission_classes = [IsAuthenticated, IsAdminUser]

        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        delete_consultation_job(instance)

    @action(
        detail=True,
        methods=["get"],
        url_path="demographic-options",
        permission_classes=[IsAuthenticated, CanSeeConsultation | IsAdminUser],
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
        methods=["post"],
        url_path="setup",
        url_name="setup",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def setup_consultation(self, request) -> Response:
        """
        Set up a new consultation by importing base data from S3.

        Imports: respondents, questions, responses
        """
        try:
            input_serializer = ConsultationSetupSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)

            validated = input_serializer.validated_data

            jobs.import_consultation.delay(
                consultation_name=validated["consultation_name"],
                consultation_code=validated["consultation_code"],
                user_id=request.user.id,
            )

            return Response(
                {"message": "Consultation setup job started successfully"},
                status=status.HTTP_202_ACCEPTED,
            )
        except serializers.ValidationError as e:
            sentry_sdk.capture_exception(e)
            return Response(
                {"message": "An error occurred while starting the import"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return Response(
                {"message": "An error occurred while starting the import"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="find-themes",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def find_themes(self, request, pk=None) -> Response:
        """
        Submit AWS batch job to find themes for each free-text question.

        The found themes are automatically saved to the database as candidate
        themes when the job completes.
        (See: lambda/import_candidate_themes/import_candidate_themes_handler.py)

        URL: /api/consultations/{consultation_id}/find-themes/
        """
        try:
            consultation = self.get_object()

            free_text_questions = consultation.question_set.filter(has_free_text=True)
            if not free_text_questions.exists():
                return Response(
                    {
                        "error": f"Consultation '{consultation.code}' has no free-text questions",
                        "detail": "ThemeFinder can only process consultations with free-text responses",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            batch.submit_job(
                job_type="FIND_THEMES",
                consultation_code=consultation.code,
                consultation_name=consultation.title,
                user_id=request.user.id,
            )

            logger.info(
                f"Find Themes job submitted for consultation {consultation.title} by user {request.user.id}"
            )

            return Response(
                {
                    "message": f"Find Themes job started for consultation '{consultation.title}'",
                    "consultation_id": consultation.id,
                    "consultation_code": consultation.code,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        except Exception as e:
            logger.exception(
                f"Error starting Find Themes job for consultation {consultation.title}: {e}"
            )
            sentry_sdk.capture_exception(e)
            return Response(
                {
                    "error": "Failed to start Find Themes job",
                    "detail": str(e) if settings.DEBUG else "An unexpected error occurred",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="assign-themes",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def assign_themes(self, request, pk=None) -> Response:
        """
        Export finalised themes to S3 and submit AWS batch job to assign themes
        to responses.

        The response annotationes are automatically saved to the database when
        the job completes.
        (See: lambda/import_response_annotations/import_response_annotations_handler.py)

        URL: /api/consultations/{consultation_id}/assign-themes/
        """

        consultation = self.get_object()

        # For each question, ensure generic themes exist
        for question in consultation.question_set.filter(has_free_text=True):
            SelectedTheme.objects.get_or_create(
                question=question,
                name="Other",
                defaults={
                    "description": "The response discusses an issue not covered by the listed themes"
                },
            )
            SelectedTheme.objects.get_or_create(
                question=question,
                name="No Reason Given",
                defaults={
                    "description": "The response does not provide a substantive answer to the question"
                },
            )

        # Export all themes to S3
        try:
            export_selected_themes_to_s3(consultation)
        except ValueError as e:
            return Response(
                {
                    "error": "No selected themes found",
                    "detail": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return Response(
                {
                    "error": "Failed to export themes to S3",
                    "detail": str(e) if settings.DEBUG else "Export failed",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Submit AWS Batch job to assign themes
        try:
            batch.submit_job(
                job_type="ASSIGN_THEMES",
                consultation_code=consultation.code,
                consultation_name=consultation.title,
                user_id=request.user.id,
            )
        except Exception as e:
            sentry_sdk.capture_exception(e)
            return Response(
                {
                    "error": "Failed to submit job to assign themes",
                    "detail": str(e) if settings.DEBUG else "Job submission failed",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Update consultation stage
        consultation.stage = Consultation.Stage.THEME_MAPPING
        consultation.save(update_fields=["stage"])

        return Response(
            {
                "message": f"Assign Themes job started for consultation '{consultation.title}'",
                "consultation_id": str(consultation.id),
                "consultation_code": consultation.code,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="export",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def submit_consultation_export(self, request) -> Response:
        """
        Submit consultation export.
        """
        try:
            input_serializer = ConsultationExportSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)

            validated = input_serializer.validated_data

            for id in validated["question_ids"]:
                try:
                    logger.info("Exporting theme audit data - sending to queue")
                    export_user_theme_job.delay(question_id=UUID(id), s3_key=validated["s3_key"])
                except Exception:
                    return Response(
                        {
                            "message": f"An error occurred while processing question export for question {id}"
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            return Response({"message": "Export job completed"}, status=status.HTTP_200_OK)
        except serializers.ValidationError:
            return Response(
                {"message": "An error occurred while starting the export"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"message": "An error occurred while starting the export"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["get"],
        url_path="folders",
        url_name="folders",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def get_consultation_folders(self, request) -> Response:
        """
        Get S3 folders and their matching consultations in the database.

        Stage query param:
        - 'setup': Return S3 folders without consultations (for creating new consultations)
        - 'find-themes': Return consultations with S3 folders (for finding themes)
        - 'assign-themes': Return consultations with S3 folders (for assigning themes)

        URL: /api/consultations/folders?stage={STAGE}
        """
        # Validate query parameters
        query_serializer = ConsultationFolderQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        stage = query_serializer.validated_data.get("stage")

        # Get all S3 folder codes
        s3_codes = s3.get_consultation_folders()

        if not s3_codes:
            return Response([])

        # Build a dict mapping code -> list of consultations (handles one-to-many relationship)
        consultations_by_code: dict[str, list[dict[str, Any]]] = {}
        for c in Consultation.objects.filter(code__in=s3_codes).values("id", "code", "title"):
            code = c["code"]
            if code not in consultations_by_code:
                consultations_by_code[code] = []
            consultations_by_code[code].append({"id": str(c["id"]), "title": c["title"]})

        if stage == "setup":
            # Return only S3 folder names without consultations, sorted by name
            s3_folders = [code for code in s3_codes if code not in consultations_by_code]
            return Response(sorted(s3_folders))
        else:
            # Return only consultations that have S3 folders, sorted by title then code
            consultations = []
            for code in consultations_by_code:
                for consultation in consultations_by_code[code]:
                    consultations.append(
                        {
                            "id": consultation["id"],
                            "code": code,
                            "title": consultation["title"],
                        }
                    )
            consultations.sort(key=lambda x: (x["title"], x["code"]))
            return Response(consultations)

    @action(
        detail=True,
        methods=["post"],
        url_path="add-users",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def add_users(self, request, pk=None) -> Response:
        """
        Add multiple users to this consultation
        Expected payload: {"emails": ["email1", "email2", ...]}
        """
        try:
            consultation = self.get_object()
        except Http404:
            return Response({"error": "Consultation not found"}, status=status.HTTP_404_NOT_FOUND)

        emails = request.data.get("emails", [])

        if not isinstance(emails, list) or not emails:
            return Response(
                {"error": "emails must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            users = User.objects.filter(email__in=emails)
            found_emails = set(user.email for user in users)
            non_existent_emails = [email for email in emails if email not in found_emails]

            if users.exists():
                consultation.users.add(*users)

            return Response(
                {
                    "message": f"Added {users.count()} users to consultation",
                    "added_count": users.count(),
                    "non_existent_emails": non_existent_emails,
                    "total_requested": len(emails),
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["delete"],
        url_path="users/(?P<user_id>[^/.]+)",
        url_name="remove-user",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def remove_user(self, request, pk=None, user_id=None) -> Response:
        """
        Remove a user from this consultation
        URL: /api/consultations/{consultation_id}/users/{user_id}/
        """
        try:
            consultation = self.get_object()
        except Http404:
            return Response({"error": "Consultation not found"}, status=status.HTTP_404_NOT_FOUND)

        if not user_id:
            return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate user_id is numeric as we have to rely on regex checks
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid user ID provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(pk=user_id_int)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if not consultation.users.filter(id=user.id).exists():
            return Response(
                {"error": "User is not assigned to this consultation"},
                status=status.HTTP_404_NOT_FOUND,
            )

        consultation.users.remove(user)

        return Response(
            {"message": f"Successfully removed user {user.email} from consultation"},
            status=status.HTTP_200_OK,
        )
