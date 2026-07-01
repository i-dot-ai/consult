import statistics
from collections import Counter, defaultdict
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
from consultations.constants import NO_REASON_GIVEN_THEME_NAME, OTHER_THEME_NAME
from consultations.models import (
    Consultation,
    DemographicOption,
    Question,
    Respondent,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)
from consultations.test_support.load_test_fixtures import (
    create_data_from_fixtures,
    delete_data_from_fixtures,
)
from data_pipeline import jobs
from data_pipeline.sync.selected_themes import export_selected_themes_to_s3
from hosting_environment import HostingEnvironment
from ingest.jobs import (
    delete_consultation_job,
)

logger = settings.LOGGER

EVALUATION_BENCHMARK_F1 = 0.75
EVALUATION_MIN_SAMPLE_SIZE = 30


def compute_response_f1(ai_themes, current_themes):
    """Compute F1 for a single response."""
    true_positives = len(ai_themes & current_themes)
    false_positives = len(ai_themes - current_themes)
    false_negatives = len(current_themes - ai_themes)
    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0.0
    )
    if (precision + recall) == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def compute_f1_stats(f1_scores):
    """Compute mean F1 with 95% confidence interval from per-response scores."""
    if not f1_scores:
        return None
    n = len(f1_scores)
    mean = statistics.mean(f1_scores)
    if n < EVALUATION_MIN_SAMPLE_SIZE:
        return {
            "mean": round(mean, 2),
            "ci_lower": None,
            "ci_upper": None,
            "approximate": True,
        }
    std = statistics.stdev(f1_scores)
    if std == 0:
        return {
            "mean": round(mean, 2),
            "ci_lower": None,
            "ci_upper": None,
            "approximate": False,
        }
    margin = 1.96 * (std / (n**0.5))
    return {
        "mean": round(mean, 2),
        "ci_lower": round(max(0, mean - margin), 2),
        "ci_upper": round(min(1, mean + margin), 2),
        "approximate": False,
    }


def get_evaluation_status(sample_size, f1):
    """Determine evaluation status based on sample size and F1 score."""
    if f1 is None or sample_size < EVALUATION_MIN_SAMPLE_SIZE:
        return "insufficient_data"
    if f1["mean"] < EVALUATION_BENCHMARK_F1:
        return "below_benchmark"
    return "meets_benchmark"


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
            filtered_respondent_ids = filtered_responses.values("respondent_id").distinct()
            through_table = Respondent.demographics.through
            counts = dict(
                through_table.objects.filter(respondent_id__in=filtered_respondent_ids)
                .values_list("demographicoption_id")
                .annotate(c=Count("id"))
                .values_list("demographicoption_id", "c")
            )
            data = [
                {
                    "id": opt["id"],
                    "field_name": opt["field_name"],
                    "field_value": opt["field_value"],
                    "count": counts.get(opt["id"], 0),
                }
                for opt in options.values("id", "field_name", "field_value").order_by(
                    "field_name", "field_value"
                )
            ]
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

            if consultation.stage != Consultation.Stage.SETUP:
                return Response(
                    {
                        "error": f"Consultation '{consultation.code}' not in setup stage",
                        "detail": "ThemeFinder can only process consultations in the setup stage",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
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
        permission_classes=[IsAuthenticated, CanSeeConsultation | IsAdminUser],
    )
    def assign_themes(self, request, pk=None) -> Response:
        """
        Export selected themes to S3 and submit AWS batch job to assign them to responses.

        Adds the default "Other" and "No Reason Given" themes, exports all selected
        themes to S3, submits the ASSIGN_THEMES batch job (which assigns themes to
        responses as ResponseAnnotation records), and advances the consultation to
        the ASSIGNING_THEMES stage.

        URL: /api/consultations/{consultation_id}/assign-themes/
        """

        consultation = self.get_object()

        if consultation.stage != Consultation.Stage.FINALISING_THEMES:
            return Response(
                {
                    "error": "Consultation must be in the Finalising Themes stage before assigning themes"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        for question in consultation.question_set.filter(has_free_text=True):
            SelectedTheme.objects.get_or_create(
                question=question,
                name=OTHER_THEME_NAME,
                defaults={
                    "description": "The response discusses an issue not covered by the listed themes"
                },
            )
            SelectedTheme.objects.get_or_create(
                question=question,
                name=NO_REASON_GIVEN_THEME_NAME,
                defaults={
                    "description": "The response does not provide a substantive answer to the question"
                },
            )

        try:
            export_selected_themes_to_s3(consultation)
        except ValueError as e:
            return Response(
                {"error": "No selected themes found for at least one question.", "detail": str(e)},
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

        # We only want to show consultations in the setup stage for the find-themes view
        consultations_filter = (
            Q(code__in=s3_codes, stage=Consultation.Stage.SETUP)
            if stage == "find-themes"
            else Q(code__in=s3_codes)
        )

        for c in Consultation.objects.filter(consultations_filter).values("id", "code", "title"):
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
        questions_without_themes = sorted(
            q["question_number"]
            for q in questions
            if q["status"] not in ("will_import", "has_existing_themes")
        )
        warnings = {
            "unmatched_source_questions": unmatched_source,
            "questions_without_themes": questions_without_themes,
        }

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

        if questions_without_themes:
            return Response(
                {
                    "error": (
                        "Cannot import: target questions "
                        f"{questions_without_themes} would have no selected themes"
                    ),
                    "questions": questions,
                    "warnings": warnings,
                },
                status=status.HTTP_400_BAD_REQUEST,
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

    @action(
        detail=True,
        methods=["get"],
        url_path="evaluation",
        permission_classes=[IsAuthenticated, IsAdminUser],
    )
    def evaluation(self, request, pk=None):
        """
        Evaluation stats for a consultation: responses read, edited, and F1 score.
        Admin only.

        F1 is computed as a sample-average (per-response F1, then mean) with 95%
        confidence intervals via normal approximation. Two variants are returned:
        one including all themes, one excluding generic themes ("No Reason Given", "Other").
        """

        consultation = self.get_object()
        free_text_questions = Question.objects.filter(consultation=consultation, has_free_text=True)

        user_ids_param = request.query_params.get("user_ids")
        if user_ids_param:
            user_ids = [uid.strip() for uid in user_ids_param.split(",") if uid.strip()]
            read_by_filter = Q(response__responsereadby__user_id__in=user_ids)
        else:
            read_by_filter = Q(response__responsereadby__user__is_staff=False)

        generic_themes = set(
            SelectedTheme.objects.filter(
                question__consultation=consultation,
            )
            .filter(
                Q(name__iexact=NO_REASON_GIVEN_THEME_NAME) | Q(name__iexact=OTHER_THEME_NAME)
            )
            .values_list("id", flat=True)
        )

        all_read_annotations = list(
            ResponseAnnotation.objects.filter(
                response__question__in=free_text_questions,
            )
            .filter(read_by_filter)
            .distinct()
            .prefetch_related("responseannotationtheme_set")
            .select_related("response")
        )

        deleted_themes_by_annotation = defaultdict(set)
        for h in ResponseAnnotationTheme.history.filter(
            response_annotation__in=all_read_annotations,
            history_type="-",
            assigned_by__isnull=True,
        ).values("response_annotation_id", "theme_id"):
            deleted_themes_by_annotation[h["response_annotation_id"]].add(h["theme_id"])

        annotations_by_question = defaultdict(list)
        for annotation in all_read_annotations:
            annotations_by_question[annotation.response.question_id].append(annotation)

        all_f1_scores = []
        all_f1_scores_all_themes = []
        questions = []

        for question in free_text_questions:
            read_response_annotations = annotations_by_question.get(question.id, [])

            question_f1_scores = []
            question_f1_scores_all_themes = []
            edited_response_ids = set()

            for response_annotation in read_response_annotations:
                surviving_ai_themes = set(
                    rat.theme_id
                    for rat in response_annotation.responseannotationtheme_set.all()
                    if rat.assigned_by_id is None
                )
                deleted_ai_themes = deleted_themes_by_annotation.get(response_annotation.id, set())
                original_themes = surviving_ai_themes | deleted_ai_themes

                current_themes = set(
                    rat.theme_id for rat in response_annotation.responseannotationtheme_set.all()
                )

                if original_themes != current_themes:
                    edited_response_ids.add(response_annotation.response_id)

                if original_themes or current_themes:
                    f1_all_themes = compute_response_f1(original_themes, current_themes)
                    question_f1_scores_all_themes.append(f1_all_themes)

                original_excl = original_themes - generic_themes
                current_excl = current_themes - generic_themes
                if original_excl or current_excl:
                    f1 = compute_response_f1(original_excl, current_excl)
                    question_f1_scores.append(f1)

            all_f1_scores.extend(question_f1_scores)
            all_f1_scores_all_themes.extend(question_f1_scores_all_themes)

            responses_read = len({ra.response_id for ra in read_response_annotations})
            f1_stats = compute_f1_stats(question_f1_scores)
            f1_all_themes_stats = compute_f1_stats(question_f1_scores_all_themes)

            questions.append(
                {
                    "id": str(question.id),
                    "number": question.number,
                    "text": question.text,
                    "status": get_evaluation_status(len(question_f1_scores), f1_stats),
                    "responses": question.free_text_response_count,
                    "responses_read": responses_read,
                    "responses_edited": len(edited_response_ids),
                    "f1": f1_stats,
                    "f1_all_themes": f1_all_themes_stats,
                }
            )

        total_response_count = sum(q["responses"] for q in questions)
        total_responses_read = sum(q["responses_read"] for q in questions)
        total_responses_edited = sum(q["responses_edited"] for q in questions)

        summary_f1 = compute_f1_stats(all_f1_scores)
        summary_f1_all_themes = compute_f1_stats(all_f1_scores_all_themes)

        available_users = (
            User.objects.filter(
                responsereadby__response__question__consultation=consultation,
                is_staff=False,
            )
            .distinct()
            .values_list("id", "email")
        )

        return Response(
            {
                "id": str(consultation.id),
                "title": consultation.title,
                "config": {
                    "benchmark_f1": EVALUATION_BENCHMARK_F1,
                    "min_sample_size": EVALUATION_MIN_SAMPLE_SIZE,
                },
                "users": [{"id": str(uid), "email": email} for uid, email in available_users],
                "summary": {
                    "status": get_evaluation_status(len(all_f1_scores), summary_f1),
                    "responses": total_response_count,
                    "responses_read": total_responses_read,
                    "responses_edited": total_responses_edited,
                    "f1": summary_f1,
                    "f1_all_themes": summary_f1_all_themes,
                },
                "questions": questions,
            }
        )
