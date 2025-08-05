import django_filters

from .. import models


class QuestionFilter(django_filters.FilterSet):
    has_themes = django_filters.BooleanFilter(method="filter_has_themes")

    def filter_has_themes(self, queryset, name, value):
        """Filter questions based on whether they have themes or not"""
        # If value is None or not provided, return unfiltered queryset
        if value is None:
            return queryset

        return queryset.filter(theme__isnull=not value)

    class Meta:
        model = models.Question
        fields = ["has_free_text", "has_themes"]
