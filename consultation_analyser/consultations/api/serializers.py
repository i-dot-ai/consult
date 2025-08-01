from rest_framework import serializers

from consultation_analyser.consultations.models import (
    Consultation,
    MultiChoiceAnswer,
    Question,
)


class MultiChoiceAnswerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MultiChoiceAnswer
        fields = ["answer"]


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


class ThemeDetailSerializer(serializers.Serializer):
    """Serializer for individual theme details within cross-cutting themes"""

    theme_id = serializers.CharField()
    theme_name = serializers.CharField()
    theme_key = serializers.CharField()
    theme_description = serializers.CharField()
    question_number = serializers.IntegerField()
    question_total_responses = serializers.IntegerField()
    mention_count = serializers.IntegerField()


class CrossCuttingThemeSerializer(serializers.Serializer):
    """Serializer for individual cross-cutting theme"""

    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    unique_respondents_count = serializers.IntegerField()
    unique_respondents_percentage = serializers.FloatField()
    questions = serializers.ListField(child=serializers.IntegerField())
    total_mentions = serializers.IntegerField()
    themes = ThemeDetailSerializer(many=True)


class CrossCuttingThemesResponseSerializer(serializers.Serializer):
    """Serializer for cross-cutting themes API response"""

    consultation_id = serializers.CharField()
    consultation_title = serializers.CharField()
    total_respondents = serializers.IntegerField()
    cross_cutting_themes = CrossCuttingThemeSerializer(many=True)
