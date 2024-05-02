from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .. import models


@login_required
def index(request: HttpRequest) -> HttpResponse:
    # TODO - in future, would restrict to all consultations for user
    consultations = models.Consultation.objects.all()
    context = {"consultations": consultations}
    return render(request, "all-consultations.html", context)


def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug)
    context = {"questions": questions}
    return render(request, "consultation.html", context)
