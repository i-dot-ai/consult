from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from consultation_analyser.consultations import dummy_data, models
from consultation_analyser.hosting_environment import HostingEnvironment
from consultation_analyser.pipeline.processing import run_processing_pipeline


@staff_member_required
def index(request: HttpRequest) -> HttpResponse:
    if request.POST:
        try:
            dummy_data.DummyConsultation(include_themes=False, number_questions=10)
            # Assume that the consultation generated is the latest one.
            # Likely to be true as this is only used in testing/dev environments.
            consultation = models.Consultation.objects.all().order_by("created_at").last()
            if consultation.name.startswith("Dummy consultation"):  # Double-check it's a dummy one.
                user = request.user
                consultation.users.add(user)
            messages.success(request, "A dummy consultation has been generated")
        except RuntimeError as error:
            messages.error(request, error.args[0])
    consultations = models.Consultation.objects.all()
    context = {"consultations": consultations, "development_env": HostingEnvironment.is_development_environment()}
    return render(request, "support_console/all-consultations.html", context=context)


@staff_member_required
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    consultation = models.Consultation.objects.get(slug=consultation_slug)
    if request.POST:
        run_processing_pipeline(consultation)
        messages.success(request, "Themes have been generated for this consultation")
    themes_for_consultation = models.Theme.objects.filter(question__section__consultation=consultation)
    number_of_themes = themes_for_consultation.count()
    number_of_themes_with_summaries = themes_for_consultation.exclude(summary="").count()
    context = {
        "consultation": consultation,
        "number_of_themes": number_of_themes,
        "number_of_themes_with_summaries": number_of_themes_with_summaries,
    }
    return render(request, "support_console/consultation.html", context=context)
