from django.shortcuts import render
from django.http import HttpRequest
from .models import Question


def show_question(request: HttpRequest, slug: str):
    context = {"question": Question.objects.filter(slug=slug).first()}
    return render(request, "show_question.html", context)
