from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max
from django.http import HttpRequest
from django.shortcuts import render

from .. import models
from .decorators import user_can_see_consultation
from .filters import get_applied_filters, get_filtered_responses, get_filtered_themes


def get_special_case_themes(
    data: dict, consultation_slug: str, section_slug: str, question_slug: str
) -> dict:
    outlier_id = None
    no_response_id = None
    outlier_count = None
    no_response_count = None

    chosen_theme_id = data.get("theme", "All")
    if chosen_theme_id != "All":
        chosen_theme = models.Theme.objects.get(id=chosen_theme_id)
        if chosen_theme.is_outlier:
            outlier_id = chosen_theme_id
            outlier_count = models.Answer.objects.filter(theme=chosen_theme).count()
        elif chosen_theme.is_no_response:
            no_response_id = chosen_theme_id
            no_response_count = models.Answer.objects.filter(theme=chosen_theme).count()
    else:
        try:
            outlier_theme = models.Theme.objects.get(
                question__slug=question_slug,
                question__section__slug=section_slug,
                question__section__consultation__slug=consultation_slug,
                is_outlier=True,
            )
            outlier_id = outlier_theme.id
            outlier_count = models.Answer.objects.filter(theme=outlier_theme).count()
        except models.Theme.DoesNotExist:
            pass
        try:
            no_response_theme = models.Theme.objects.get(
                question__slug=question_slug,
                question__section__slug=section_slug,
                question__section__consultation__slug=consultation_slug,
                is_no_response=True,
            )
            no_response_id = no_response_theme.id
            no_response_count = models.Answer.objects.filter(theme=no_response_theme).count()
        except models.Theme.DoesNotExist:
            pass
    output = {
        "outlier_id": outlier_id,
        "no_response_id": no_response_id,
        "outlier_count": outlier_count,
        "no_response_count": no_response_count,
    }
    return output


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    data = request.GET
    special_case_info = get_special_case_themes(
        data=data,
        consultation_slug=consultation_slug,
        section_slug=section_slug,
        question_slug=question_slug,
    )

    question = models.Question.objects.get(
        slug=question_slug,
        section__slug=section_slug,
        section__consultation__slug=consultation_slug,
    )
    applied_filters = get_applied_filters(request)
    responses = get_filtered_responses(question, applied_filters)
    filtered_themes = (
        get_filtered_themes(question, responses, applied_filters)
        .annotate(answer_count=Count("answer"))
        .order_by("-answer_count")
    )

    # Get counts
    total_responses = responses.count()
    multiple_choice_questions = {}
    if total_responses:
        if question.multiple_choice_options:
            for multichoice in question.multiple_choice_options:
                resps = []
                for opt in multichoice["options"]:
                    count = responses.filter_multiple_choice(
                        question=multichoice["question_text"], answer=opt
                    ).count()
                    resps.append(
                        {"answer": opt, "percent": round((float(count) / total_responses) * 100)}
                    )

                multiple_choice_questions[multichoice["question_text"]] = resps

    highest_theme_count = filtered_themes.aggregate(Max("answer_count"))["answer_count__max"]

    context = {
        "consultation_slug": consultation_slug,
        "question": question,
        "multiple_choice_questions": multiple_choice_questions,
        "responses": responses,
        "themes": filtered_themes,
        "highest_theme_count": highest_theme_count,
        "total_responses": total_responses,
        "applied_filters": applied_filters,
    }
    context.update(special_case_info)
    return render(request, "consultations/questions/show.html", context)
