from django.http import HttpRequest
from django.shortcuts import render

from .. import models


def home(request: HttpRequest):
    questions = models.QuestionOld.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "static_pages/home.html", context)
