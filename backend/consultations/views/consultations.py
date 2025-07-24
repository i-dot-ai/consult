import logging

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from consultation_analyser.consultations import models

from .decorators import user_can_see_consultation, user_can_see_dashboards

logger = logging.getLogger("upload")


def index(request: HttpRequest) -> HttpResponse:
    user = request.user
    consultations_for_user = models.Consultation.objects.filter(users=user)
    context = {
        "consultations": consultations_for_user,
        "user_has_dashboard_access": user.has_dashboard_access,
    }
    return render(request, "consultations/consultations/index.html", context)


@user_can_see_dashboards
@user_can_see_consultation
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    # Dashboard page
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    questions = models.Question.objects.filter(consultation=consultation).order_by("number")

    all_questions = []
    for question in questions:
        question_dict = {"question": question}

        # Handle free text questions
        if question.has_free_text:
            question_dict["free_text_question_part"] = question  # For template compatibility

        non_null_responses_count = (
            models.Response.objects.filter(question=question)
            .exclude(free_text__isnull=True)
            .exclude(chosen_options__isnull=True)
            .count()
        )
        question_dict["number_responses"] = non_null_responses_count

        # Handle multiple choice questions
        if question.has_multiple_choice:
            question_dict["multiple_option_question_part"] = question

            # Get option counts
            responses = models.Response.objects.filter(question=question).values("chosen_options")
            option_counts: dict[str, int] = {}
            for response in responses:
                if options := response.get("chosen_options"):
                    for option in options:
                        option_counts[option] = option_counts.get(option, 0) + 1

            question_dict["multiple_option_counts"] = option_counts

        all_questions.append(question_dict)

    # What is the right number per page?
    pagination = Paginator(all_questions, 2)
    page_index = request.GET.get("page", "1")
    current_page = pagination.page(page_index)
    paginated_questions = current_page.object_list

    context = {
        "consultation": consultation,
        "pagination": current_page,
        "questions_list": paginated_questions,
        "all_questions_list": all_questions,
    }
    return render(request, "consultations/consultations/show.html", context)
