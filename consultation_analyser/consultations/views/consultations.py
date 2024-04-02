from django.shortcuts import render
from django.http import HttpRequest

from .. import models


def show_questions(request: HttpRequest):
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "consultation.html", context)
