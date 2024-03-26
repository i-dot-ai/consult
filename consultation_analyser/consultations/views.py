from django.shortcuts import render
from django.http import HttpRequest
from . import models

from tests.factories import ConsultationFactory, AnswerFactory


def home(request: HttpRequest):
    if request.POST:
        # TODO - can't import from factories
        dummy_consultation = ConsultationFactory(with_question=True)
        dummy_question = models.Question.objects.filter(consultation=dummy_consultation).first()
        dummy_question.has_free_text = True
        dummy_question.save()
        AnswerFactory(questions=dummy_question, theme=None)
        consultation_slug = dummy_consultation.slug
        # TODO - to be replaced by redirect
        return render(request, "home.html", context)

    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "home.html", context)


def show_question(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    themes_for_question = models.Theme.objects.filter(answer__question=question)
    # TODO - probably want counts etc.
    context = {"question": question, "themes": themes_for_question}
    return render(request, "show_question.html", context)
