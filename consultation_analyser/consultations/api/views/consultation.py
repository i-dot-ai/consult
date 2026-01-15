import logging
from uuid import UUID

import sentry_sdk
from django.conf import settings
from django.db.models import Count
from django.http import Http404
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

import consultation_analyser.data_pipeline.batch as batch
from consultation_analyser.authentication.models import User
from consultation_analyser.consultations.api.permissions import (
    CanSeeConsultation,
    HasDashboardAccess,
)
from consultation_analyser.consultations.api.serializers import (
    ConsultationExportSerializer,
    ConsultationFolderSerializer,
    ConsultationImportAnnotationsSerializer,
    ConsultationImportCandidateThemesSerializer,
    ConsultationImportImmutableSerializer,
    ConsultationImportSerializer,
    ConsultationSerializer,
    DemographicOptionSerializer,
)
from consultation_analyser.consultations.export_user_theme import export_user_theme_job
from consultation_analyser.consultations.models import (
    Consultation,
    DemographicOption,
    SelectedTheme,
)
from consultation_analyser.support_console import ingest
from consultation_analyser.data_pipeline.sync.selected_themes import export_selected_themes_to_s3
from consultation_analyser.support_console.views.consultations import (
    delete_consultation_job,
    import_candidate_themes_job,
    import_consultation_job,
    import_immutable_data_job,
    import_response_annotations_job,
)

logger = settings.LOGGER


class ConsultationViewSet(ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, CanSeeConsultation | IsAdminUser]
    filterset_fields = ["code"]
    http_method_names = ["get", "patch", "delete", "post"]

    def get_queryset(self):
        scope = self.request.query_params.get("scope")
        if scope == "assigned":
            return Consultation.objects.filter(users=self.request.user).order_by("-created_at")
        elif self.request.user.is_staff:
            return Consultation.objects.all().order_by("-created_at")
        return Consultation.objects.filter(users=self.request.user).order_by("-created_at")

    def perform_destroy(self, instance):
        delete_consultation_job(instance)

    @action(
        detail=True,
        methods=["get"],
        url_path="demographic-options",
        permission_classes=[HasDashboardAccess],
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
        url_path="import",
        permission_classes=[HasDashboardAccess],
    )
    def submit_consultation_import(self, request) -> Response:
        """
        Submit consultation import.
        """
        try:
            input_serializer = ConsultationImportSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)

            validated = input_serializer.validated_data

            import_consultation_job.delay(
                consultation_name=validated["consultation_name"],
                consultation_code=validated["consultation_code"],
                timestamp=validated["timestamp"],
                current_user_id=request.user.id,
                sign_off=input_serializer.get_sign_off(),
            )

            return Response(
                {"message": "Import job started successfully"}, status=status.HTTP_202_ACCEPTED
            )
        except serializers.ValidationError:
            return Response(
                {"message": "An error occurred while starting the import"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            return Response(
                {"message": "An error occurred while starting the import"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=False,
        methods=["post"],
        url_path="import-immutable",
        permission_classes=[IsAdminUser],
    )
    def import_immutable_data(self, request) -> Response:
        """
        Import immutable consultation data from S3.
        """
        try:
            input_serializer = ConsultationImportImmutableSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)

            validated = input_serializer.validated_data

            import_immutable_data_job.delay(
                consultation_name=validated["consultation_name"],
                consultation_code=validated["consultation_code"],
                user_id=request.user.id,
            )

            return Response(
                {"message": "Immutable data import job started successfully"},
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
        permission_classes=[IsAdminUser],
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
        permission_classes=[IsAdminUser],
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
        permission_classes=[HasDashboardAccess],
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
                    logging.info("Exporting theme audit data - sending to queue")
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
        permission_classes=[HasDashboardAccess],
    )
    def get_consultation_folders(self, request) -> Response:
        """
        get consultation folders.
        """
        consultation_folders = ingest.get_consultation_codes()

        serializer = ConsultationFolderSerializer(consultation_folders, many=True)

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path="add-users",
        permission_classes=[IsAdminUser],
    )
    def add_users(self, request, pk=None) -> Response:
        """
        Add multiple users to this consultation
        Expected payload: {"user_ids": ["uuid1", "uuid2", ...]}
        """
        try:
            consultation = self.get_object()
        except Http404:
            return Response({"error": "Consultation not found"}, status=status.HTTP_404_NOT_FOUND)

        user_ids = request.data.get("user_ids", [])

        if not isinstance(user_ids, list) or not user_ids:
            return Response(
                {"error": "user_ids must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            users = User.objects.filter(id__in=user_ids)
            found_user_count = users.count()

            if found_user_count != len(user_ids):
                return Response(
                    {"error": f"Only {found_user_count} of {len(user_ids)} users found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid user IDs provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        consultation.users.add(*users)

        return Response(
            {"message": f"Successfully added {found_user_count} users to consultation"},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path="users/(?P<user_id>[^/.]+)",
        url_name="remove-user",
        permission_classes=[IsAdminUser],
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
