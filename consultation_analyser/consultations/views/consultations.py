from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .. import models
from .decorators import user_can_see_consultation


@login_required
def index(request: HttpRequest) -> HttpResponse:
    consultations = request.user.consultation_set.all()
    context = {"consultations": consultations}
    return render(request, "all-consultations.html", context)


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug)
    context = {"questions": questions}
    return render(request, "consultation.html", context)
