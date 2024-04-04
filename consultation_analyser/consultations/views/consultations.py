from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from consultation_analyser.hosting_environment import HostingEnvironment

from .. import models


def show_questions(request: HttpRequest):
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "consultation.html", context)


# TODO placeholder view for testing - needs updating
def show_consultation(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug)
    show_button = HostingEnvironment.is_dev() or HostingEnvironment.is_local() or HostingEnvironment.is_test()
    context = {"questions": questions, "show_button": show_button}
    if request.POST:
        pass
        # TODO - generate themes
    return render(request, "show_consultation.html", context)


def create_dummy_data(request: HttpRequest) -> HttpResponse:
    if request.POST:
        pass
        #
    return render(request, "create_dummy_data.html")
