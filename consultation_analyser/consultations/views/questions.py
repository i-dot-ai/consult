from django.core.paginator import Paginator
from django.db.models import Count, Max
from django.http import HttpRequest
from django.shortcuts import render
from waffle.decorators import waffle_switch

from .. import models


@waffle_switch("CONSULTATION_PROCESSING")
def show(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    themes_for_question = models.Theme.objects.filter(answer__question=question).annotate(answer_count=Count("answer"))

    # Get counts
    total_responses = models.Answer.objects.filter(question=question).count()
    highest_theme_count = themes_for_question.aggregate(Max("answer_count"))["answer_count__max"]

    context = {
        "question": question,
        "themes": themes_for_question,
        "highest_theme_count": highest_theme_count,
        "total_responses": total_responses,
    }
    return render(request, "show_question.html", context)
