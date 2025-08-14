from rest_framework import serializers

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations.models import (
    Consultation,
    CrossCuttingTheme,
    MultiChoiceAnswer,
    Question,
    Response,
    ResponseAnnotation,
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

    class Meta:
        model = Theme
        fields = ["id", "name", "description"]


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


class ResponseSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(source="respondent.themefinder_id")
    free_text_answer_text = serializers.CharField(source="free_text")
    demographic_data = serializers.JSONField(source="respondent.demographics")
    themes = ThemeSerializer(source="annotation.themes", many=True, read_only=True, default=[])
    multiple_choice_answer = serializers.SlugRelatedField(
        source="chosen_options", slug_field="text", many=True, read_only=True
    )
    evidenceRich = serializers.SerializerMethodField()

    def get_evidenceRich(self, obj) -> bool:
        try:
            return obj.annotation.evidence_rich == ResponseAnnotation.EvidenceRich.YES
        except AttributeError:
            return False

    class Meta:
        model = Response
        fields = [
            "identifier",
            "free_text_answer_text",
            "demographic_data",
            "themes",
            "multiple_choice_answer",
            "evidenceRich",
        ]
