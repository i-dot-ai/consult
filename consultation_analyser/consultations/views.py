from django.shortcuts import render
from django.http import HttpRequest

from . import models
from consultation_analyser.consultations import ml_pipeline


def generate_dummy_consultation():
    # TODO - well, generate a dummy consultation
    return


def home(request: HttpRequest):
    consultations = models.Consultation.objects.all()
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions, "consultations": consultations}
    if request.POST:
        generate_dummy_consultation()
        # TODO - can't import from factories
        # dummy_consultation = ConsultationFactory(with_question=True)
        # dummy_question = models.Question.objects.filter(consultation=dummy_consultation).first()
        # dummy_question.has_free_text = True
        # dummy_question.save()
        # AnswerFactory(questions=dummy_question, theme=None)
        # consultation_slug = dummy_consultation.slug
        # # TODO - to be replaced by redirect
        return render(request, "home.html", context)

    return render(request, "home.html", context)


def show_question(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    themes_for_question = models.Theme.objects.filter(answer__question=question)
    # TODO - probably want counts etc.
    context = {"question": question, "themes": themes_for_question}
    return render(request, "show_question.html", context)


# TODO - replace with a proper view! This is for testing.
def show_consultation(request: HttpRequest, consultation_slug: str):
    if request.POST:
        ml_pipeline.dummy_save_themes_for_consultation(consultation_slug)
    consultation = models.Consultation.objects.get(slug=consultation_slug)
    questions = models.Question.objects.filter(section__consultation=consultation)
    context = {"consultation": consultation, "questions": questions}
    return render(request, "show_consultation.html", context)
