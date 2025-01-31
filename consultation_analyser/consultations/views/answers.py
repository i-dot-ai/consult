from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from .. import models
from .decorators import user_can_see_consultation


@user_can_see_consultation
def index(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
):
    # For now, just display free text parts of the question
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)

    question = models.Question.objects.get(
        slug=question_slug,
        consultation=consultation,
    )

    # Assume that there is only one free text response
    free_text_question_part = models.QuestionPart.objects.filter(
        question=question, type=models.QuestionPart.QuestionType.FREE_TEXT
    ).first()
    if free_text_question_part:
        free_text_answers = models.Answer.objects.filter(question_part=free_text_question_part)
        total_responses = free_text_answers.count()
    else:
        free_text_answers = models.Answer.objects.none()
        total_responses = 0

    # pagination
    pagination = Paginator(free_text_answers, 5)
    page_index = request.GET.get("page", "1")
    current_page = pagination.page(page_index)
    paginated_responses = current_page.object_list

    context = {
        "consultation_name": consultation.title,
        "consultation_slug": consultation_slug,
        "question": question,
        "free_text_question_part": free_text_question_part,
        "responses": paginated_responses,
        "total_responses": total_responses,
        "pagination": current_page,
    }

    return render(request, "consultations/answers/index.html", context)


@user_can_see_consultation
def show(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
    response_id: int,
):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(models.Question, slug=question_slug, consultation=consultation)
    response = get_object_or_404(models.Answer, id=response_id)

    # TODO: update with QuestionPart
    all_theme_mappings = models.ThemeMapping.get_latest_theme_mappings_for_question_part(
        part=response.question_part
    )
    all_themes = models.Theme.objects.filter(id__in=all_theme_mappings.values("theme"))
    existing_themes = models.ThemeMapping.objects.filter(answer=response).values_list(
        "theme", flat=True
    )

    if request.method == "POST":
        requested_themes = request.POST.getlist("theme")
        existing_mappings = models.ThemeMapping.objects.filter(answer=response)

        # themes to delete
        existing_mappings.exclude(theme_id__in=requested_themes).delete()

        # themes to add
        themes_to_add = set(requested_themes).difference([str(theme) for theme in existing_themes])
        for theme_id in themes_to_add:
            models.ThemeMapping.objects.create(answer=response, theme_id=theme_id, stance="")

        # flag
        response.is_theme_mapping_audited = True
        response.save()

        return redirect(
            "show_next_response", consultation_slug=consultation_slug, question_slug=question_slug
        )

    elif request.method == "GET":
        context = {
            "consultation_name": consultation.title,
            "consultation_slug": consultation_slug,
            "question": question,
            "response": response,
            "all_themes": all_themes,
            "existing_themes": existing_themes,  #  update this key
            "date_created": datetime.strftime(response.created_at, "%d %B %Y"),
        }

        return render(request, "consultations/answers/show.html", context)


@user_can_see_consultation
def show_next(request: HttpRequest, consultation_slug: str, question_slug: str):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(models.Question, slug=question_slug, consultation=consultation)

    def handle_no_responses():
        context = {
            "consultation_name": consultation.title,
            "consultation_slug": consultation_slug,
            "question": question,
        }
        return render(request, "consultations/answers/no_responses.html", context)

    # Get the question part with themes
    try:
        question_part_with_themes = question.questionpart_set.get(
            type=models.QuestionPart.QuestionType.FREE_TEXT
        )
    except ObjectDoesNotExist:
        return handle_no_responses()

    # Get the next response that has not been checked
    next_response = (
        models.Answer.objects.filter(
            question_part=question_part_with_themes, is_theme_mapping_audited=False
        )
        .order_by("?")
        .first()
    )

    if next_response:
        return redirect(
            "show_response",
            consultation_slug=consultation_slug,
            question_slug=question_slug,
            response_id=next_response.id,
        )

    return handle_no_responses()
