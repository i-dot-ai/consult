from django.db.models import Count, QuerySet
from django.http import HttpRequest

from .. import models


def get_applied_filters(request: HttpRequest) -> dict[str, str]:
    return {
        "keyword": request.GET.get("keyword", ""),
        "theme": request.GET.get("theme", "All"),
        "opinion": request.GET.get("opinion", "All"),
    }


# TODO: rename this to Answers
def get_filtered_responses(question: models.Question, applied_filters: dict[str, str]) -> QuerySet:
    queryset = models.Answer.objects.filter(question=question, free_text__contains=applied_filters["keyword"])
    if applied_filters["theme"] != "All":
        queryset = queryset.filter(theme=applied_filters["theme"])
    if applied_filters["opinion"] != "All":
        queryset = queryset.filter_multiple_choice(
            question=question.multiple_choice_options[0]["question_text"], answer=applied_filters["opinion"]
        )
    return queryset


def get_filtered_themes(
    question: models.Question, filtered_answers: QuerySet, applied_filters: dict[str, str]
) -> QuerySet:
    queryset = models.Theme.objects.filter(answer__question=question).annotate(answer_count=Count("answer"))
    if applied_filters["theme"] != "All":
        queryset = queryset.filter(id=applied_filters["theme"])
    if applied_filters["opinion"] != "All":
        unique_themes = filtered_answers.values("theme").distinct()
        unique_themes_list = [item["theme"] for item in unique_themes]
        queryset = queryset.filter(id__in=unique_themes_list)
    return queryset
