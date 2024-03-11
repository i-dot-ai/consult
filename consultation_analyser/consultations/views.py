from django.shortcuts import render
from django.http import HttpRequest
from .models import Question


def home(request: HttpRequest):
    return render(request, "home.html")


def show_question(request: HttpRequest, slug: str):
    context = {"question": Question.objects.filter(slug=slug).first()}
    return render(request, "show_question.html", context)


def question_summary(request: HttpRequest, consultation_slug: str, question_slug: str):
    # Question.objects.get(section__consultation__slug=consultation_slug, slug=question_slug)
    question = Question.objects.filter(slug=question_slug)
    question = question[0]
    # TODO - get themes from DB

    themes = {}
    context = {"question": question, "themes": themes}
    return render(request, "question-summary.html", context)
