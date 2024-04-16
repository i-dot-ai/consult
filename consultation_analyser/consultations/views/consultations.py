from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from waffle.decorators import waffle_switch

from .. import models


@waffle_switch("CONSULTATION_PROCESSING")
def show_questions(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug)
    context = {"questions": questions}
    return render(request, "consultation.html", context)
