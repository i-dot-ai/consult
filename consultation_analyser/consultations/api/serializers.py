from typing import Any

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations.models import (
    Consultation,
    CrossCuttingTheme,
    DemographicOption,
    MultiChoiceAnswer,
    Question,
    Respondent,
    Response,
    ResponseAnnotationTheme,
    SelectedTheme,
)


class UserSerializer(serializers.ModelSerializer):
    has_dashboard_access = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = ["id", "email", "has_dashboard_access", "is_staff", "created_at"]


class MultiChoiceAnswerSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    response_count = serializers.SerializerMethodField()

    def get_response_count(self, obj) -> int:
        return obj.response_set.count()

    class Meta:
        model = MultiChoiceAnswer
        fields = ["id", "text", "response_count"]


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    question_text = serializers.CharField(source="text")
    multiple_choice_answer = MultiChoiceAnswerSerializer(
        many=True, source="multichoiceanswer_set", read_only=True
    )
    proportion_of_audited_answers = serializers.ReadOnlyField()
    total_responses = serializers.SerializerMethodField()

    def get_total_responses(self, obj) -> int:
        return obj.response_set.count()

    class Meta:
        model = Question
        fields = [
            "id",
            "number",
            "total_responses",
            "question_text",
            "slug",
            "number",
            "has_free_text",
            "has_multiple_choice",
            "multiple_choice_answer",
            "proportion_of_audited_answers",
            "theme_status",
        ]


class ConsultationSerializer(serializers.HyperlinkedModelSerializer):
    users = serializers.SlugRelatedField(slug_field="email", many=True, queryset=User.objects.all())

    class Meta:
        model = Consultation
        fields = ["id", "title", "slug", "stage", "users"]


class DemographicOptionsSerializer(serializers.Serializer):
    name = serializers.CharField(source="demographics__field_name")
    value = serializers.JSONField(source="demographics__field_value")
    count = serializers.IntegerField()


class DemographicAggregationsSerializer(serializers.Serializer):
    demographic_aggregations = serializers.DictField(
        child=serializers.DictField(child=serializers.IntegerField())
    )


class ThemeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    key = serializers.CharField(required=False)

    class Meta:
        model = SelectedTheme
        fields = ["id", "name", "description", "key"]


class ThemeInformationSerializer(serializers.Serializer):
    themes = serializers.ListField(child=ThemeSerializer())


class ThemeAggregationsSerializer(serializers.Serializer):
    theme_aggregations = serializers.DictField(child=serializers.IntegerField())


class SelectedThemeSerializer(serializers.ModelSerializer):
    last_modified_by = serializers.SerializerMethodField()

    class Meta:
        model = SelectedTheme
        fields = ["id", "name", "description", "version", "modified_at", "last_modified_by"]

    def get_last_modified_by(self, obj):
        return obj.last_modified_by.email if obj.last_modified_by else None


class ThemeSerializer2(serializers.ModelSerializer):
    question_id = serializers.UUIDField(source="question.id")

    response_count = serializers.SerializerMethodField()

    def get_response_count(self, theme: SelectedTheme) -> int:
        return Response.objects.filter(annotation__themes=theme).count()

    class Meta:
        model = SelectedTheme
        fields = ["name", "description", "key", "question_id", "response_count"]


class CrossCuttingThemeSerializer(serializers.ModelSerializer):
    themes = ThemeSerializer2(many=True, source="selectedtheme_set", read_only=True)
    response_count = serializers.SerializerMethodField()

    def get_response_count(self, cross_cutting_theme: CrossCuttingTheme) -> int:
        return Response.objects.filter(annotation__themes__parent=cross_cutting_theme).count()

    class Meta:
        model = CrossCuttingTheme
        fields = ["name", "description", "themes", "response_count"]


class ResponseAnnotationThemeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="theme.id")
    name = serializers.CharField(required=False, source="theme.name")
    description = serializers.CharField(required=False, source="theme.description")
    key = serializers.CharField(required=False, source="theme.key")
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
        fields = ["id", "assigned_by", "name", "description", "key"]


class ResponseSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(source="respondent.themefinder_id", read_only=True)
    respondent_id = serializers.UUIDField(source="respondent.id", read_only=True)
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
    is_edited = serializers.BooleanField(source="annotation.is_edited")
    question_id = serializers.UUIDField()

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

    class Meta:
        model = Response
        fields = [
            "id",
            "identifier",
            "respondent_id",
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
        ]


class DemographicOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="field_name")
    value = serializers.JSONField(source="field_value")

    class Meta:
        model = DemographicOption
        fields = ["name", "value"]


class RespondentSerializer(serializers.ModelSerializer):
    demographics = DemographicOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Respondent
        fields = ["id", "themefinder_id", "demographics", "name"]
