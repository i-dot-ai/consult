import datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consultation_analyser.hosting_environment import HostingEnvironment

from .. import dummy_data, ml_pipeline, models


def show_questions(request: HttpRequest):
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "consultation.html", context)


# TODO placeholder - needs updating
def show_consultation(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    consultation = models.Consultation.objects.get(slug=consultation_slug)
    questions = models.Question.objects.filter(section__consultation=consultation)
    context = {"questions": questions, "consultation": consultation}
    if request.POST:
        # TODO - to be updated with the proper call to save themes
        ml_pipeline.save_themes_for_consultation(consultation.id)
    return render(request, "show_consultation.html", context)


def create_dummy_data(request: HttpRequest) -> HttpResponse:
    # For testing, only on dev/local/test
    if request.POST:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        name = f"Dummy Consultation generated at {timestamp}"
        slug = f"consultation-slug-{timestamp}"
        dummy_data.DummyConsultation(name=name, slug=slug, include_themes=False)
        latest_consultation = models.Consultation.objects.order_by("created_at").last()  # assume one just created
        return redirect("show_consultation", consultation_slug=latest_consultation.slug)
    return render(request, "create_dummy_data.html")
