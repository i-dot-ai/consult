from pathlib import Path
from typing import Any, ClassVar

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from authentication.models import User
from consultations.models import (
    CandidateTheme,
    CandidateThemeResponse,
    Consultation,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotationTheme,
    SelectedTheme,
)


class UserSerializer(serializers.ModelSerializer):
    emails = serializers.ListSerializer(child=serializers.EmailField(), required=False)

    class Meta:
        model = User
        fields: ClassVar[list] = ["id", "email", "is_staff", "created_at", "emails"]

    def to_internal_value(self, data):
        if email := data.get("email"):
            data["email"] = email.lower()

        if emails := data.get("emails"):
            data["emails"] = [email.lower() for email in emails]
        return super().to_internal_value(data)

    def validate_is_staff(self, value):
        request = self.context.get("request")

        if self.instance and request and request.user == self.instance and value is False:
            raise serializers.ValidationError("You cannot remove admin privileges from yourself")

        return value


class ConsultationSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()
    is_assigned = serializers.SerializerMethodField()

    class Meta:
        model = Consultation
        fields: ClassVar[list] = [
            "id",
            "title",
            "code",
            "stage",
            "data_source",
            "users",
            "created_by",
            "created_at",
            "started_at",
            "closed_at",
            "is_owner",
            "is_assigned",
            "running_job",
        ]

    def get_is_owner(self, obj) -> bool | None:
        if obj.created_by_id is None:
            return None
        return obj.created_by_id == self.context["request"].user.id

    def get_is_assigned(self, obj) -> bool:
        user_id = self.context["request"].user.id
        return any(user.id == user_id for user in obj.users.all())


class ConsultationCreateSerializerV2(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields: ClassVar[list] = ["id", "title"]
        read_only_fields: ClassVar[list] = ["id"]


class ConsultationFileUploadSerializerV2(serializers.Serializer):
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MiB
    ALLOWED_EXTENSIONS: ClassVar[set[str]] = {".csv", ".xlsx"}

    file = serializers.FileField(write_only=True)

    def validate_file(self, value):
        extension = Path(value.name).suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError("File must be a CSV or XLSX file.")
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError("File must not exceed 200 MiB.")
        return value


class ConsultationDeepValidationSerializerV2(serializers.Serializer):
    MAX_FILE_SIZE = 200 * 1024 * 1024

    file = serializers.FileField(write_only=True, allow_empty_file=True)

    def validate_file(self, value):
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError("File must not exceed 200 MiB.")
        return value


class ConsultationUpdateSerializerV2(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields: ClassVar[list] = ["id", "title", "data_source"]
        read_only_fields: ClassVar[list] = ["id"]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # Pipeline jobs write stage and running_job concurrently; a full save would revert them.
        if validated_data:
            instance.save(update_fields=[*validated_data, "modified_at"])
        return instance


class DemographicOptionMergeSerializer(serializers.Serializer):
    new_value = serializers.CharField(allow_blank=False, trim_whitespace=True)
    demographic_options = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=2,
    )

    def validate_demographic_options(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Demographic option IDs must be unique.")
        return value


class DemographicOptionMutationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="field_name")
    value = serializers.JSONField(source="field_value", required=False)
    new_value = serializers.CharField(write_only=True, required=False, allow_blank=False)
    count = serializers.IntegerField(source="response_count", read_only=True)

    def validate(self, attrs):
        new_value = attrs.pop("new_value", None)
        if new_value is not None:
            if "field_value" in attrs:
                raise serializers.ValidationError("Use either 'value' or 'new_value', not both.")
            attrs["field_value"] = new_value

        if self.instance is None and "field_value" not in attrs:
            raise serializers.ValidationError({"value": "This field is required."})

        consultation = (
            self.instance.consultation
            if self.instance is not None
            else self.context["consultation"]
        )
        field_name = attrs.get(
            "field_name",
            self.instance.field_name if self.instance is not None else None,
        )
        field_value = attrs.get(
            "field_value",
            self.instance.field_value if self.instance is not None else None,
        )
        matching_options = DemographicOption.objects.filter(
            consultation=consultation,
            field_name=field_name,
            field_value=field_value,
        )
        if self.instance is not None:
            matching_options = matching_options.exclude(pk=self.instance.pk)
        if matching_options.exists():
            raise serializers.ValidationError(
                {"value": "A demographic option with this value already exists."}
            )
        return attrs

    class Meta:
        model = DemographicOption
        fields: ClassVar[list] = ["id", "name", "value", "new_value", "count"]
        read_only_fields: ClassVar[list] = ["id", "count"]
class QuestionSetupSerializer(serializers.ModelSerializer):
    # Blank is a model-level default, not a type a question can be set to.
    type = serializers.ChoiceField(
        choices=Question.QuestionType.choices, allow_null=True, allow_blank=False, required=False
    )
    # Hybrid is this link, not a type (ADR-0006).
    closed_question = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(), allow_null=True, required=False
    )
    response_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Question
        fields: ClassVar[list] = [
            "id",
            "number",
            "text",
            "type",
            "closed_question",
            "status",
            "response_count",
        ]
        read_only_fields: ClassVar[list] = ["id", "number", "status", "response_count"]

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Question wording cannot be blank.")
        return value

    def validate_closed_question(self, value):
        if value is None:
            return value
        if value.pk == self.instance.pk:
            raise serializers.ValidationError("A question cannot be linked to itself.")
        if value.consultation_id != self.instance.consultation_id:
            raise serializers.ValidationError(
                "The closed question must belong to the same consultation."
            )
        if value.type != Question.QuestionType.CLOSED:
            raise serializers.ValidationError("Only a closed question can be linked.")
        return value

    def validate(self, attrs):
        question_type = attrs.get("type", self.instance.type)
        closed_question = attrs.get("closed_question", self.instance.closed_question)
        if closed_question is not None and question_type != Question.QuestionType.OPEN:
            raise serializers.ValidationError(
                {"closed_question": "Only an open question can be linked to a closed question."}
            )
        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        update_fields = list(validated_data)
        if "type" in validated_data:
            instance.status = (
                Question.ThemeStatus.DRAFT
                if instance.type is None
                else Question.ThemeStatus.CONFIGURED
            )
            update_fields.append("status")
        if update_fields:
            instance.save(update_fields=[*update_fields, "modified_at"])
        return instance


class MultiChoiceAnswerSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    response_count = serializers.SerializerMethodField()

    def get_response_count(self, obj) -> int:
        # When filters are applied, the view annotates a dynamic count
        if hasattr(obj, "prefetched_response_count"):
            return obj.prefetched_response_count
        return obj.response_count

    class Meta:
        model = MultiChoiceAnswer
        fields: ClassVar[list] = ["id", "text", "response_count"]


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    question_text = serializers.CharField(source="text")
    multiple_choice_answer = MultiChoiceAnswerSerializer(
        many=True, source="multichoiceanswer_set", read_only=True
    )
    proportion_of_audited_answers = serializers.SerializerMethodField()

    def get_proportion_of_audited_answers(self, obj) -> float:
        if not obj.free_text_response_count:
            return 0
        reviewed = getattr(obj, "prefetched_reviewed_responses", 0) or 0
        return reviewed / obj.free_text_response_count

    class Meta:
        model = Question
        fields: ClassVar[list] = [
            "id",
            "number",
            "total_response_count",
            "free_text_response_count",
            "multi_choice_response_count",
            "question_text",
            "has_free_text",
            "has_multiple_choice",
            "multiple_choice_answer",
            "proportion_of_audited_answers",
            "theme_status",
        ]
        read_only_fields: ClassVar[list] = [
            "total_response_count",
            "free_text_response_count",
            "multi_choice_response_count",
        ]


class DemographicAggregationsSerializer(serializers.Serializer):
    demographic_aggregations = serializers.DictField(
        child=serializers.DictField(child=serializers.IntegerField())
    )


class ThemeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    key = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = SelectedTheme
        fields: ClassVar[list] = ["id", "name", "description", "key"]


class ThemeInformationSerializer(serializers.Serializer):
    themes = serializers.ListField(child=ThemeSerializer())


class ResponseThemeInformationSerializer(serializers.Serializer):
    selected_themes = ThemeSerializer(many=True)
    all_themes = ThemeSerializer(many=True)


class QuestionThemeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    description = serializers.CharField()
    count = serializers.IntegerField()

    class Meta:
        model = SelectedTheme
        fields: ClassVar[list] = ["id", "name", "description", "count"]


class ThemeAggregationsSerializer(serializers.Serializer):
    theme_aggregations = serializers.DictField(child=serializers.IntegerField())


class SelectedThemeSerializer(serializers.ModelSerializer):
    last_modified_by = serializers.SerializerMethodField()

    class Meta:
        model = SelectedTheme
        fields: ClassVar[list] = [
            "id",
            "name",
            "description",
            "version",
            "modified_at",
            "last_modified_by",
        ]
        read_only_fields: ClassVar[list] = ["id", "version", "modified_at", "last_modified_by"]

    def get_last_modified_by(self, obj):
        return obj.last_modified_by.email if obj.last_modified_by else None


class ThemeWithResponseCountSerializer(serializers.ModelSerializer):
    question_id = serializers.UUIDField(source="question.id")

    response_count = serializers.SerializerMethodField()

    def get_response_count(self, theme: SelectedTheme) -> int:
        return theme.prefetched_response_count

    class Meta:
        model = SelectedTheme
        fields: ClassVar[list] = ["name", "description", "key", "question_id", "response_count"]


class CandidateThemeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = CandidateTheme
        fields: ClassVar[list] = [
            "id",
            "name",
            "description",
            "children",
            "selectedtheme_id",
        ]

    def get_children(self, obj):
        # Use prefetched children if available (set by Prefetch with to_attr)
        if hasattr(obj, "prefetched_children"):
            return CandidateThemeSerializer(obj.prefetched_children, many=True).data

        # Fallback for single object serialization (e.g., retrieve action)
        children = CandidateTheme.objects.filter(parent=obj)
        return CandidateThemeSerializer(children, many=True).data


class CandidateThemeResponseSerializer(serializers.ModelSerializer):
    free_text = serializers.CharField(source="response.free_text", read_only=True)
    response_id = serializers.UUIDField(source="response.id", read_only=True)

    class Meta:
        model = CandidateThemeResponse
        fields: ClassVar[list] = ["response_id", "free_text"]


class ResponseAnnotationThemeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="theme.id")
    name = serializers.CharField(required=False, source="theme.name")
    description = serializers.CharField(required=False, source="theme.description")
    key = serializers.CharField(required=False, allow_null=True, source="theme.key")
    assigned_by = serializers.SerializerMethodField()

    def to_internal_value(self, data):
        pk = super().to_internal_value(data)["theme"]["id"]
        try:
            return SelectedTheme.objects.get(pk=pk)
        except SelectedTheme.DoesNotExist:
            detail = f'Invalid pk "{pk}" - object does not exist.'
            raise ValidationError(detail=detail, code="invalid")

    def get_assigned_by(self, obj):
        if obj.assigned_by is None:
            return "AI"
        return obj.assigned_by.email

    class Meta:
        model = ResponseAnnotationTheme
        fields: ClassVar[list] = ["id", "assigned_by", "name", "description", "key"]


class DemographicOptionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField(source="field_name")
    value = serializers.JSONField(source="field_value")
    count = serializers.IntegerField(required=False)


class RespondentSerializer(serializers.ModelSerializer):
    demographics = DemographicOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Respondent
        fields: ClassVar[list] = ["id", "themefinder_id", "demographics", "name"]


class ResponseSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(source="respondent.themefinder_id", read_only=True)
    respondent_id = serializers.UUIDField(source="respondent.id", read_only=True)
    respondent = RespondentSerializer(read_only=True)
    free_text_answer_text = serializers.CharField(source="free_text", read_only=True)
    demographic_data = serializers.SerializerMethodField(read_only=True)
    themes = ResponseAnnotationThemeSerializer(
        source="annotation.responseannotationtheme_set", many=True
    )
    multiple_choice_answer = serializers.SlugRelatedField(
        source="chosen_options", slug_field="text", many=True, read_only=True
    )
    evidenceRich = serializers.BooleanField(source="annotation.evidence_rich", default=False)
    sentiment = serializers.CharField(source="annotation.sentiment")
    human_reviewed = serializers.BooleanField(source="annotation.human_reviewed")
    is_flagged = serializers.BooleanField(read_only=True)
    is_edited = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    question_id = serializers.UUIDField()

    def get_is_edited(self, obj):
        return obj.annotation_is_edited or obj.annotation_has_human_assigned_themes

    def get_is_read(self, obj):
        return getattr(obj, "is_read_by_user", False)

    def get_demographic_data(self, obj) -> dict[str, Any] | None:
        return {d.field_name: d.field_value for d in obj.respondent.demographics.all()}

    def update(self, instance: Response, validated_data):
        if annotation := validated_data.get("annotation"):
            if "human_reviewed" in annotation:
                human_reviewed = annotation["human_reviewed"]
                instance.annotation.human_reviewed = human_reviewed
                instance.annotation.reviewed_by = (
                    self.context["request"].user if human_reviewed else None
                )
                instance.annotation.reviewed_at = timezone.now() if human_reviewed else None

            if "evidence_rich" in annotation:
                instance.annotation.evidence_rich = annotation["evidence_rich"]

            if "responseannotationtheme_set" in annotation:
                instance.annotation.set_human_reviewed_themes(
                    themes=annotation["responseannotationtheme_set"],
                    user=self.context["request"].user,
                )

            if "sentiment" in annotation:
                instance.annotation.sentiment = annotation["sentiment"]

            instance.annotation.save()

        instance.refresh_from_db()
        return instance

    def to_representation(self, instance):
        # this hack exists to ensure that an empty list is returned when there is no ResponseAnnotation
        representation = super().to_representation(instance)
        if representation["themes"] is None:
            representation["themes"] = []
        return representation

    class Meta:
        model = Response
        fields: ClassVar[list] = [
            "id",
            "identifier",
            "respondent_id",
            "respondent",
            "question_id",
            "free_text_answer_text",
            "demographic_data",
            "themes",
            "multiple_choice_answer",
            "evidenceRich",
            "sentiment",
            "human_reviewed",
            "is_flagged",
            "is_edited",
            "is_read",
        ]


class ConsultationFolderQuerySerializer(serializers.Serializer):
    stage = serializers.ChoiceField(
        choices=["setup", "find-themes"],
        required=True,
    )


class ConsultationSetupSerializer(serializers.Serializer):
    consultation_name = serializers.CharField(required=True, max_length=255)
    consultation_code = serializers.CharField(required=True, max_length=255)


class ConsultationExportSerializer(serializers.Serializer):
    s3_key = serializers.CharField(max_length=255, default="", allow_null=True)
    question_ids = serializers.ListSerializer(child=serializers.CharField())


class ImportFinalisedThemesSerializer(serializers.Serializer):
    source_consultation_id = serializers.UUIDField()


class TokenSerializer(serializers.Serializer):
    internal_access_token = serializers.CharField()
