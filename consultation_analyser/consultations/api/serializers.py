from typing import Any

from django.utils import timezone
from rest_framework import serializers

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
    total_responses = serializers.IntegerField(
        read_only=True,
        source="response_count",
        required=False,
    )

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
    demographic_options = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField())
    )


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


class FilterSerializer(serializers.Serializer):
    """Serializer for query parameter filters"""

    sentimentFilters = serializers.CharField(required=False, allow_blank=True)
    themeFilters = serializers.CharField(required=False, allow_blank=True)
    evidenceRich = serializers.BooleanField(required=False)
    searchValue = serializers.CharField(required=False)
    searchMode = serializers.ChoiceField(choices=["semantic", "keyword"], required=False)
    demoFilters = serializers.ListField(child=serializers.CharField(), required=False)
    # Pagination parameters
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=50, min_value=1, max_value=100)


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


class RelatedThemeSerializer(serializers.PrimaryKeyRelatedField):
    """this is a variation on the PrimaryKeyRelatedField where
    representation is actually that of the ThemeSerializer
    """

    queryset = Theme.objects.all()

    def to_internal_value(self, data):
        data = ThemeSerializer().to_internal_value(data)["id"]
        return super().to_internal_value(data)

    def to_representation(self, value):
        return ThemeSerializer().to_representation(value)


class ResponseSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(source="respondent.themefinder_id", read_only=True)
    free_text_answer_text = serializers.CharField(source="free_text", read_only=True)
    demographic_data = serializers.SerializerMethodField(read_only=True)
    themes = RelatedThemeSerializer(source="annotation.themes", many=True, default=[])
    multiple_choice_answer = serializers.SlugRelatedField(
        source="chosen_options", slug_field="text", many=True, read_only=True
    )
    evidenceRich = serializers.BooleanField(source="annotation.evidence_rich", default=False)
    sentiment = serializers.CharField(source="annotation.sentiment")
    human_reviewed = serializers.BooleanField(source="annotation.human_reviewed")
    flagged_by = serializers.SlugRelatedField(
        source="annotation.flagged_by", slug_field="email", many=True, read_only=True
    )

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

            if "themes" in annotation:
                ResponseAnnotationTheme.objects.filter(
                    response_annotation=instance.annotation
                ).delete()
                for theme in annotation["themes"]:
                    ResponseAnnotationTheme.objects.create(
                        response_annotation=instance.annotation,
                        theme=theme,
                        is_original_ai_assignment=False,
                        assigned_by=self.context["request"].user,
                    )
                instance.annotation.refresh_from_db()

            if "sentiment" in annotation:
                instance.annotation.sentiment = annotation["sentiment"]

            instance.annotation.save()

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
            "flagged_by",
        ]
