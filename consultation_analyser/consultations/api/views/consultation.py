import logging
from uuid import UUID

import sentry_sdk
from django.db.models import Count
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

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
from consultation_analyser.consultations.models import Consultation, DemographicOption
from consultation_analyser.support_console import ingest
from consultation_analyser.support_console.views.consultations import (
    delete_consultation_job,
    import_candidate_themes_job,
    import_consultation_job,
    import_immutable_data_job,
    import_response_annotations_job,
)


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
        detail=False,
        methods=["post"],
        url_path="import-candidate-themes",
        permission_classes=[IsAdminUser],
    )
    def import_candidate_themes(self, request) -> Response:
        """
        Import candidate themes from S3.
        """
        try:
            input_serializer = ConsultationImportCandidateThemesSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)

            validated = input_serializer.validated_data

            import_candidate_themes_job.delay(
                consultation_code=validated["consultation_code"],
                timestamp=validated["timestamp"],
            )

            return Response(
                {"message": "Candidate themes import job started successfully"},
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
        detail=False,
        methods=["post"],
        url_path="import-annotations",
        permission_classes=[IsAdminUser],
    )
    def import_annotations(self, request) -> Response:
        """
        Import response annotations from S3.
        """
        try:
            input_serializer = ConsultationImportAnnotationsSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)

            validated = input_serializer.validated_data

            import_response_annotations_job.delay(
                consultation_code=validated["consultation_code"],
                timestamp=validated["timestamp"],
            )

            return Response(
                {"message": "Response annotations import job started successfully"},
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
        url_path="add-user",
        permission_classes=[HasDashboardAccess],
    )
    def add_user(self, request, pk=None, user_pk=None) -> Response:
        """
        add a user to this consultation
        """
        try:
            consultation = self.get_object()
            user = User.objects.get(pk=user_pk)
            consultation.users.add(user)
            consultation.save()
        except (User.DoesNotExist, Consultation.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_201_CREATED)
