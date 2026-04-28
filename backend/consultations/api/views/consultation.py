from typing import Any

import sentry_sdk
from django.conf import settings
from django.db.models import Count, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import Http404
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

import data_pipeline.batch as batch
import data_pipeline.s3 as s3
from authentication.models import User
from consultations.api.filters import get_filtered_responses
from consultations.api.permissions import (
    CanSeeConsultation,
)
from consultations.api.serializers import (
    ConsultationFolderQuerySerializer,
    ConsultationSerializer,
    ConsultationSetupSerializer,
    DemographicOptionSerializer,
)
from consultations.dummy_data import create_dummy_consultation_from_yaml
from consultations.models import (
    Consultation,
    DemographicOption,
    SelectedTheme,
)
from consultations.models import (
    Response as ConsultationResponse,
)
from data_pipeline import jobs
from data_pipeline.sync.candidate_themes import export_candidate_themes_to_s3
from data_pipeline.sync.selected_themes import export_selected_themes_to_s3
from hosting_environment import HostingEnvironment
from ingest.jobs import (
    delete_consultation_job,
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
            return (
                Consultation.objects.filter(users=self.request.user)
                .prefetch_related("users")
                .order_by("-created_at")
            )
        elif self.request.user.is_staff:
            return Consultation.objects.prefetch_related("users").order_by("-created_at")
        return (
            Consultation.objects.filter(users=self.request.user)
            .prefetch_related("users")
            .order_by("-created_at")
        )

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
        """
        Enqueue consultation deletion job to worker container
        """
        delete_consultation_job.delay(instance.id)

    def destroy(self, request, *args, **kwargs):
        """
        Delete consultation asynchronously via worker.

        Returns 202 Accepted to indicate the deletion has been queued
        and will be processed asynchronously.
        """
        instance = self.get_object()
        self.perform_destroy(instance)

        return Response(
            {
                "message": f"Deletion of consultation '{instance.title}' has been queued",
                "consultation_id": str(instance.id),
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="demographics",
        permission_classes=[IsAuthenticated, CanSeeConsultation | IsAdminUser],
    )
    def demographics(self, request, pk=None):
        """
        Demographic options with counts, optionally filtered by question/theme/etc.
        """
        self.get_object()

        options = DemographicOption.objects.filter(consultation_id=pk)

        filter_params = [
            "themeFilters",
            "demographics",
            "evidenceRich",
            "unseenResponsesOnly",
            "is_flagged",
            "multiple_choice_answer",
            "searchValue",
        ]
        question_id = request.query_params.get("question_id")
        has_filters = any(request.query_params.get(p) for p in filter_params)

        if has_filters:
            # Get filtered respondent IDs once - much faster than Exists subquery per option
            filtered_responses = get_filtered_responses(
                request.query_params, pk, request=request
            )
            filtered_respondent_ids = list(
                filtered_responses.values_list("respondent_id", flat=True).distinct()
            )
            options = options.filter(
                respondent__id__in=filtered_respondent_ids
            ).annotate(count=Count("respondent", distinct=True))
        elif question_id:
            # Scope counts to respondents who answered this question
            respondent_demographics_table = DemographicOption.respondent_set.through
            options = options.annotate(
                count=Coalesce(
                    Subquery(
                        respondent_demographics_table.objects.filter(
                            demographicoption_id=OuterRef("pk"),
                            respondent_id__in=ConsultationResponse.objects.filter(
                                question_id=question_id
                            ).values("respondent_id"),
                        )
                        .values("demographicoption_id")
                        .annotate(c=Count("respondent_id", distinct=True))
                        .values("c")
                    ),
                    Value(0),
                )
            )
        else:
            options = options.annotate(count=Count("respondent"))

        data = options.values("id", "field_name", "field_value", "count").order_by(
            "field_name", "field_value"
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
                model_name=consultation.model_name,
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
        Export themes to S3 and submit AWS batch job to assign themes to responses.

        Behaviour depends on consultation stage:
        - FINALISING_THEMES / THEME_SIGN_OFF: exports candidate themes and assigns
          them to responses (CandidateThemeResponse), without changing stage.
        - Other stages: exports selected themes and assigns them to responses
          (ResponseAnnotation), advancing stage to THEME_MAPPING.

        URL: /api/consultations/{consultation_id}/assign-themes/
        """

        consultation = self.get_object()

        is_finalising = consultation.stage in (
            Consultation.Stage.FINALISING_THEMES,
            Consultation.Stage.THEME_SIGN_OFF,
        )

        if is_finalising:
            # During finalising: assign candidate themes to responses
            try:
                export_candidate_themes_to_s3(consultation)
            except ValueError as e:
                return Response(
                    {"error": "No candidate themes found", "detail": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                sentry_sdk.capture_exception(e)
                return Response(
                    {
                        "error": "Failed to export candidate themes to S3",
                        "detail": str(e) if settings.DEBUG else "Export failed",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            try:
                batch.submit_job(
                    job_type="ASSIGN_THEMES",
                    consultation_code=consultation.code,
                    consultation_name=consultation.title,
                    user_id=request.user.id,
                    model_name=consultation.model_name,
                    assignment_target="candidate_themes",
                )
            except Exception as e:
                sentry_sdk.capture_exception(e)
                return Response(
                    {
                        "error": "Failed to submit job to assign candidate themes",
                        "detail": str(e) if settings.DEBUG else "Job submission failed",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Stay in current stage - don't advance to THEME_MAPPING
            return Response(
                {
                    "message": f"Assign Candidate Themes job started for consultation '{consultation.title}'",
                    "consultation_id": str(consultation.id),
                    "consultation_code": consultation.code,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        # Normal flow: assign selected themes to responses
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

        try:
            export_selected_themes_to_s3(consultation)
        except ValueError as e:
            return Response(
                {"error": "No selected themes found", "detail": str(e)},
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

        try:
            batch.submit_job(
                job_type="ASSIGN_THEMES",
                consultation_code=consultation.code,
                consultation_name=consultation.title,
                user_id=request.user.id,
                model_name=consultation.model_name,
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

    @action(
        detail=False,
        methods=["post"],
        url_path="generate-test-consultation",
        permission_classes=[IsAdminUser],
    )
    def generate_test_consultations(self, request) -> Response:
        """
        Add dummy test consultation data
        URL: /api/consultations/generate-test-consultations

        Only permitted in development environments
        """

        if HostingEnvironment.is_deployed():
            return Response(
                {"error": "This endpoint is only for use in automated testing"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            logger.info("Generating dummy consultations...")
            consultation_sign_off = create_dummy_consultation_from_yaml(
                number_respondents=5, consultation_stage="theme_sign_off"
            )
            consultation_sign_off.users.add(request.user)
            consultation_analysis = create_dummy_consultation_from_yaml(
                number_respondents=5, consultation_stage="analysis"
            )
            consultation_analysis.users.add(request.user)

        except Exception as e:
            return Response(
                {"error": f"An error occurred generating example consultations: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Successfully added example consultations",
                "consultations": {
                    "sign_off": consultation_sign_off.id,
                    "analysis": consultation_analysis.id,
                },
            },
            status=status.HTTP_200_OK,
        )
