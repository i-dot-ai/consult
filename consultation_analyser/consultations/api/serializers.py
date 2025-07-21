from rest_framework import serializers


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


class RespondentDataSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    free_text_answer_text = serializers.CharField()
    demographic_data = serializers.DictField()
    themes = serializers.ListField(child=ThemeSerializer())
    multiple_choice_answer = serializers.ListField(child=serializers.CharField())
    evidenceRich = serializers.BooleanField()


class FilteredResponsesSerializer(serializers.Serializer):
    all_respondents = serializers.ListField(child=RespondentDataSerializer())
    has_more_pages = serializers.BooleanField()
    respondents_total = serializers.IntegerField()
    filtered_total = serializers.IntegerField()


class QuestionInformationSerializer(serializers.Serializer):
    question_text = serializers.CharField()
    total_responses = serializers.IntegerField()


class FilterSerializer(serializers.Serializer):
    """Serializer for query parameter filters"""
    sentimentFilters = serializers.CharField(required=False, allow_blank=True)
    themeFilters = serializers.CharField(required=False, allow_blank=True)
    themesSortDirection = serializers.ChoiceField(
        choices=["ascending", "descending"], 
        required=False
    )
    themesSortType = serializers.ChoiceField(
        choices=["frequency", "alphabetical"], 
        required=False
    )
    evidenceRich = serializers.BooleanField(required=False)
    searchValue = serializers.CharField(required=False)
    searchMode = serializers.ChoiceField(
        choices=["semantic", "keyword"], 
        required=False
    )
    demoFilters = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    # Pagination parameters
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=50, min_value=1, max_value=100)