from django.db.models import Max
from django.http import HttpRequest
from django.shortcuts import render
from waffle.decorators import waffle_switch

from .. import models
from .filters import get_applied_filters, get_filtered_responses, get_filtered_themes


@waffle_switch("CONSULTATION_PROCESSING")
def show(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    applied_filters = get_applied_filters(request)
    responses = get_filtered_responses(question, applied_filters)
    filtered_themes = get_filtered_themes(question, responses, applied_filters)

    # Get counts
    total_responses = responses.count()
    multiple_choice_responses = []
    if total_responses:
        for option in question.multiple_choice_options:
            count = responses.filter(multiple_choice_responses__contains=option).count()
            multiple_choice_responses.append({"answer": option, "percent": round((count / total_responses) * 100)})
    highest_theme_count = filtered_themes.aggregate(Max("answer_count"))["answer_count__max"]

    context = {
        "question": question,
        "multiple_choice_responses": multiple_choice_responses,
        "responses": responses,
        "themes": filtered_themes,
        "highest_theme_count": highest_theme_count,
        "total_responses": total_responses,
        "applied_filters": applied_filters,
    }
    return render(request, "show_question.html", context)
