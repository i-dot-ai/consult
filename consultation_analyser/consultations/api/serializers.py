from rest_framework import serializers

from consultation_analyser.consultations.models import (
    Consultation,
    CrossCuttingTheme,
    MultiChoiceAnswer,
    Question,
    Response,
    Theme,
)


class MultiChoiceAnswerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MultiChoiceAnswer
        fields = ["text"]


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    question_text = serializers.CharField(source="text")
    multiple_choice_options = MultiChoiceAnswerSerializer(
        many=True, source="multichoiceanswer_set", read_only=True
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


class ThemeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()


class ThemeInformationSerializer(serializers.Serializer):
    themes = serializers.ListField(child=ThemeSerializer())


class ThemeAggregationsSerializer(serializers.Serializer):
    theme_aggregations = serializers.DictField(child=serializers.IntegerField())


class FilterSerializer(serializers.Serializer):
    """Serializer for query parameter filters"""

    sentimentFilters = serializers.CharField(required=False, allow_blank=True)
    themeFilters = serializers.CharField(required=False, allow_blank=True)
    themesSortDirection = serializers.ChoiceField(
        choices=["ascending", "descending"], required=False
    )
    themesSortType = serializers.ChoiceField(choices=["frequency", "alphabetical"], required=False)
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
