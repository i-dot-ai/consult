from typing import Any

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations.models import (
    Consultation,
    CrossCuttingTheme,
    MultiChoiceAnswer,
    Question,
    Response,
    ResponseAnnotationTheme,
    Theme,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "has_dashboard_access"]


class MultiChoiceAnswerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MultiChoiceAnswer
        fields = ["text"]


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    question_text = serializers.CharField(source="text")
    multiple_choice_options = MultiChoiceAnswerSerializer(
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
            "multiple_choice_options",
            "proportion_of_audited_answers",
        ]


class ConsultationSerializer(serializers.HyperlinkedModelSerializer):
    questions = QuestionSerializer(
        source="question_set",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Consultation
        fields = ["id", "title", "slug", "questions"]


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
        model = Theme
        fields = ["id", "name", "description", "key"]


class ThemeInformationSerializer(serializers.Serializer):
    themes = serializers.ListField(child=ThemeSerializer())


class ThemeAggregationsSerializer(serializers.Serializer):
    theme_aggregations = serializers.DictField(child=serializers.IntegerField())


class ThemeSerializer2(serializers.ModelSerializer):
    question_id = serializers.UUIDField(source="question.id")

    response_count = serializers.SerializerMethodField()

    def get_response_count(self, theme: Theme) -> int:
        return Response.objects.filter(annotation__themes=theme).count()

    class Meta:
        model = Theme
        fields = ["name", "description", "key", "question_id", "response_count"]


class CrossCuttingThemeSerializer(serializers.ModelSerializer):
    themes = ThemeSerializer2(many=True, source="theme_set", read_only=True)
    response_count = serializers.SerializerMethodField()

    def get_response_count(self, cross_cutting_theme: CrossCuttingTheme) -> int:
        return Response.objects.filter(annotation__themes__parent=cross_cutting_theme).count()

    class Meta:
        model = CrossCuttingTheme
        fields = ["name", "description", "themes", "response_count"]


class MultiChoiceAnswerCount(serializers.Serializer):
    answer = serializers.CharField(source="chosen_options__text")
    response_count = serializers.IntegerField()


class ResponseAnnotationThemeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    name = serializers.CharField(required=False, source="theme.name")
    description = serializers.CharField(required=False, source="theme.description")
    key = serializers.CharField(required=False, source="theme.key")
    assigned_by = serializers.SerializerMethodField()

    def to_internal_value(self, data):
        pk = super().to_internal_value(data)["id"]
        try:
            return Theme.objects.get(pk=pk)
        except Theme.DoesNotExist:
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
                ResponseAnnotationTheme.objects.filter(
                    response_annotation=instance.annotation,
                    assigned_by=self.context["request"].user,
                ).delete()
                for theme in annotation["responseannotationtheme_set"]:
                    ResponseAnnotationTheme.objects.create(
                        response_annotation=instance.annotation,
                        theme=theme,
                        assigned_by=self.context["request"].user,
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
            "free_text_answer_text",
            "demographic_data",
            "themes",
            "multiple_choice_answer",
            "evidenceRich",
            "sentiment",
            "human_reviewed",
            "is_flagged",
        ]
