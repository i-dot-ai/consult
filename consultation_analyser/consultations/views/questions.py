from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import HttpRequest
from django.shortcuts import render

from .. import models
from .decorators import user_can_see_consultation
from .filters import get_applied_filters, get_filtered_responses, get_filtered_themes


@user_can_see_consultation
@login_required
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
        if question.multiple_choice_options:
            for multichoice in question.multiple_choice_options:
                for opt in multichoice["options"]:
                    count = responses.filter_multiple_choice(question=multichoice["question_text"], answer=opt).count()
                    multiple_choice_responses.append({"answer": opt, "percent": round((count / total_responses) * 100)})
    highest_theme_count = filtered_themes.aggregate(Max("answer_count"))["answer_count__max"]

    context = {
        "consultation_slug": consultation_slug,
        "question": question,
        "multiple_choice_responses": multiple_choice_responses,
        "responses": responses,
        "themes": filtered_themes,
        "highest_theme_count": highest_theme_count,
        "total_responses": total_responses,
        "applied_filters": applied_filters,
    }
    return render(request, "show_question.html", context)
