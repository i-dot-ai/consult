from rest_framework import serializers

from consultation_analyser.consultations.models import (
    Consultation,
    MultiChoiceAnswer,
    Question,
    Response,
    ResponseAnnotation,
    Theme,
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
