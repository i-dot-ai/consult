from collections import Counter
from typing import Any

import sentry_sdk
from django.conf import settings
from django.db import transaction
from django.db.models import Count, F, Q
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
    ImportFinalisedThemesSerializer,
)
from consultations.models import (
    Consultation,
    DemographicOption,
    Question,
    SelectedTheme,
)
from consultations.test_support.load_test_fixtures import (
    create_data_from_fixtures,
    delete_data_from_fixtures,
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
        has_filters = question_id or any(request.query_params.get(p) for p in filter_params)

        if has_filters:
            filtered_responses = get_filtered_responses(
                request.query_params, pk, question_id=question_id
            )
            filtered_respondent_ids = filtered_responses.values("respondent_id")
            options = options.annotate(
                filtered_count=Count(
                    "respondent",
                    filter=Q(respondent__in=filtered_respondent_ids),
                    distinct=True,
                )
            )
            data = options.values(
                "id", "field_name", "field_value", count=F("filtered_count")
            ).order_by("field_name", "field_value")
        else:
            data = options.values(
                "id", "field_name", "field_value", count=F("response_count")
            ).order_by("field_name", "field_value")

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
        - FINALISING_THEMES: exports candidate themes and assigns
          them to responses (CandidateThemeResponse), without changing stage.
        - Other stages: exports selected themes and assigns them to responses
          (ResponseAnnotation), advancing stage to ASSIGNING_THEMES.

        URL: /api/consultations/{consultation_id}/assign-themes/
        """

        consultation = self.get_object()

        is_finalising = consultation.stage == Consultation.Stage.FINALISING_THEMES

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

            # Stay in current stage - don't advance
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

        consultation.stage = Consultation.Stage.ASSIGNING_THEMES
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
        url_path="create-test-data",
        permission_classes=[IsAdminUser],
    )
    def create_test_data(self, request) -> Response:
        """
        Add dummy test data from fixtures
        URL: /api/consultations/create-test-data

        Only permitted in local and test environments
        """

        if HostingEnvironment.is_deployed():
            return Response(
                {"error": "This endpoint is only for use in automated testing"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if fixtures := request.data.get("fixtures", []):
            created_fixtures = create_data_from_fixtures(fixtures)

            return Response(created_fixtures)

        return Response(
            {"error": "No fixture data provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="import-finalised-themes",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def import_finalised_themes(self, request, pk=None) -> Response:
        """
        Import finalised themes from a source consultation into this (target) consultation.

        Matches questions by text between source and target. Preserves the
        original user attribution and timestamps.

        URL: POST /api/consultations/{target_consultation_id}/import-finalised-themes/
        Body: { "source_consultation_id": "<uuid>" }
        Query: ?dry_run=true to preview without making changes
        """

        input_serializer = ImportFinalisedThemesSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        target = self.get_object()
        dry_run = request.query_params.get("dry_run", "").lower() == "true"
        source_consultation_id = input_serializer.validated_data["source_consultation_id"]

        try:
            source = Consultation.objects.get(id=source_consultation_id)
        except Consultation.DoesNotExist:
            return Response(
                {"error": f"Source consultation '{source_consultation_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if source.id == target.id:
            return Response(
                {"error": "Source and target consultation cannot be the same"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        finalised_stages = {Consultation.Stage.ASSIGNING_THEMES, Consultation.Stage.ANALYSIS}
        if source.stage not in finalised_stages:
            return Response(
                {"error": "Source consultation must have finalised themes"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if target.stage in finalised_stages:
            return Response(
                {"error": "Target consultation has already finalised themes"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_questions = source.question_set.filter(has_free_text=True)
        target_questions = target.question_set.filter(has_free_text=True)

        # Detect duplicate question texts within each consultation
        source_text_counts = Counter(q.text for q in source_questions)
        target_text_counts = Counter(q.text for q in target_questions)
        duplicate_source_texts = {t for t, c in source_text_counts.items() if c > 1}
        duplicate_target_texts = {t for t, c in target_text_counts.items() if c > 1}

        source_by_text = {q.text: q for q in source_questions}
        target_by_text = {q.text: q for q in target_questions}

        source_themes_by_question: dict = {}
        for theme in SelectedTheme.objects.filter(question__in=source_questions).select_related(
            "last_modified_by"
        ):
            source_themes_by_question.setdefault(theme.question_id, []).append(theme)

        target_questions_with_themes = set(
            SelectedTheme.objects.filter(question__in=target_questions)
            .values_list("question_id", flat=True)
            .distinct()
        )

        questions = []

        for target_q in target_questions.order_by("number"):
            question_info = {
                "question_number": target_q.number,
                "question_text": target_q.text,
            }

            if target_q.text in duplicate_target_texts:
                question_info["status"] = "duplicate_in_target"
                questions.append(question_info)
                continue

            if target_q.text in duplicate_source_texts:
                question_info["status"] = "duplicate_in_source"
                questions.append(question_info)
                continue

            if target_q.text not in source_by_text:
                question_info["status"] = "no_match_in_source"
                questions.append(question_info)
                continue

            if target_q.id in target_questions_with_themes:
                question_info["status"] = "has_existing_themes"
                questions.append(question_info)
                continue

            source_q = source_by_text[target_q.text]
            themes = source_themes_by_question.get(source_q.id, [])

            if not themes:
                question_info["status"] = "no_themes_in_source"
                questions.append(question_info)
                continue

            question_info["status"] = "will_import"
            question_info["source_themes"] = [t.name for t in themes]
            questions.append(question_info)

        unmatched_source = sorted(set(source_by_text.keys()) - {q.text for q in target_questions})
        warnings = {"unmatched_source_questions": unmatched_source}

        if dry_run:
            return Response(
                {
                    "dry_run": True,
                    "source_consultation": {"id": str(source.id), "title": source.title},
                    "target_consultation": {"id": str(target.id), "title": target.title},
                    "questions": questions,
                    "warnings": warnings,
                }
            )

        # Execute the import
        imported_themes = 0
        with transaction.atomic():
            for q_info in questions:
                if q_info["status"] != "will_import":
                    continue

                target_q = target_by_text[q_info["question_text"]]
                source_q = source_by_text[q_info["question_text"]]
                themes = source_themes_by_question.get(source_q.id, [])

                for theme in themes:
                    new_theme = SelectedTheme.objects.create(
                        question=target_q,
                        name=theme.name,
                        description=theme.description,
                        key=theme.key,
                        last_modified_by=theme.last_modified_by,
                    )
                    # Preserve original timestamps from the source to maintain audit trail.
                    # QuerySet.update() is required because auto_now/auto_now_add bypass save().
                    SelectedTheme.objects.filter(pk=new_theme.pk).update(
                        created_at=theme.created_at,
                        modified_at=theme.modified_at,
                    )
                    imported_themes += 1

                target_q.theme_status = Question.ThemeStatus.CONFIRMED
                target_q.save(update_fields=["theme_status"])

            # Advance stage to FINALISING_THEMES if currently earlier in the pipeline
            earlier_stages = {Consultation.Stage.SETUP, Consultation.Stage.FINDING_THEMES}
            if target.stage in earlier_stages:
                target.stage = Consultation.Stage.FINALISING_THEMES
                target.save(update_fields=["stage"])

        # Export to S3
        try:
            export_selected_themes_to_s3(target)
        except Exception as e:
            logger.error("S3 export failed after theme import: {error}", error=str(e))
            return Response(
                {
                    "error": f"Themes were saved to the database ({imported_themes} imported) but S3 export failed: {e}",
                    "total_themes_imported": imported_themes,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info(
            "Imported {count} selected themes from '{source}' to '{target}' by user {user}",
            count=imported_themes,
            source=source.title,
            target=target.title,
            user=request.user.email,
        )

        return Response(
            {
                "dry_run": False,
                "source_consultation": {"id": str(source.id), "title": source.title},
                "target_consultation": {"id": str(target.id), "title": target.title},
                "total_themes_imported": imported_themes,
                "questions": questions,
                "warnings": warnings,
                "performed_by": request.user.email,
            }
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="delete-test-data",
        permission_classes=[IsAdminUser],
    )
    def delete_test_data(self, request) -> Response:
        """
        Delete dummy test consultation data from fixtures
        URL: /api/consultations/delete-test-data

        Only permitted in local and test environments
        """

        if HostingEnvironment.is_deployed():
            return Response(
                {"error": "This endpoint is only for use in automated testing"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if fixtures := request.data.get("fixtures", []):
            delete_data_from_fixtures(fixtures)
            return Response()

        return Response(
            {"error": "No fixture data provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )
