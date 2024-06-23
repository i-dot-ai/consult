from django.db.models import QuerySet


def remove_empty_free_text_responses(answers_qs: QuerySet):
    qs = answers_qs.exclude(free_text="").exclude(free_text__isnull=True)
    return qs


def remove_responses_with_outliers(answers_qs: QuerySet):
    qs = answers_qs.exclude(theme__is_outlier=True)
    return qs
