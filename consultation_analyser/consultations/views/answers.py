from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render

from .. import models
from .decorators import user_can_see_consultation


@user_can_see_consultation
@login_required
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
