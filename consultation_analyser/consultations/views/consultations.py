import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from consultation_analyser.consultations.models import QuestionPart, Question, Consultation, ThemeMapping
from .decorators import user_can_see_consultation

logger = logging.getLogger("upload")


def index(request: HttpRequest) -> HttpResponse:
    user = request.user
    consultations_for_user = Consultation.objects.filter(users=user)
    context = {"consultations": consultations_for_user}
    return render(request, "consultations/consultations/index.html", context)


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    # Dashboard page
    consultation = get_object_or_404(Consultation, slug=consultation_slug)
    questions = Question.objects.filter(consultation__slug=consultation_slug).order_by(
        "number"
    )

    questions_list = []
    for question in questions:
        question_dict = {"question": question}
        # Get free text question stuff
        free_text_question_part = QuestionPart.objects.filter(question=question).filter(type=QuestionPart.QuestionType.FREE_TEXT).first()
        if free_text_question_part:
            question_dict["free_text_question_part"] = free_text_question_part
            # TODO - add top themes
            # For now, just get latest theme mappings
            theme_mappings = ThemeMapping.get_latest_theme_mappings_for_question_part(free_text_question_part)
        # For now, assume that we just take the first closed question (in many cases there will be just one)
        # Just take the single option for now
        single_option_question_part = QuestionPart.objects.filter(question=question).filter(
            type=QuestionPart.QuestionType.SINGLE_OPTION
        ).first()
        if single_option_question_part:
            question_dict["single_option_question_part"] = single_option_question_part
            # TODO - add counts
        questions_list.append(question_dict)

    print("======== questions_list ===========")
    print(questions_list)

    context = {
        "all_questions": questions_list,
        "consultation": consultation,
    }
    # TODO - do something better if there is no question text, and get it from the question parts
    return render(request, "consultations/consultations/show.html", context)
