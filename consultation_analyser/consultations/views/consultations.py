from django.http import HttpRequest
from django.shortcuts import render
from waffle.decorators import waffle_switch

from .. import models


@waffle_switch("CONSULTATION_PROCESSING")
def show_questions(request: HttpRequest):
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "consultation.html", context)
