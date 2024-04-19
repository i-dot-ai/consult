from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.messages import get_messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consultation_analyser.consultations import dummy_data, models
from consultation_analyser.hosting_environment import HostingEnvironment


@staff_member_required
def support_home(request: HttpRequest):
    return render(request, "support_console/home.html")


@staff_member_required
def sign_out(request: HttpRequest):
    logout(request)
    return redirect("/")


@staff_member_required
def show_consultations(request: HttpRequest) -> HttpResponse:
    # TODO - add messages
    if request.POST:
        try:
            dummy_data.DummyConsultation(include_themes=False)
        except RuntimeError as error:
            pass
            # TODO - pass through message from the error
    consultations = models.Consultation.objects.all()
    context = {"consultations": consultations, "development_env": HostingEnvironment.is_development_environment()}
    return render(request, "support_console/all-consultations.html", context=context)


@staff_member_required
def show_consultation(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    consultation = models.Consultation.objects.get(slug=consultation_slug)
    if request.POST:
        themes_already_exist = models.Theme.objects.filter(
            answer__question__section__consultation=consultation
        ).exists()
        if not themes_already_exist:
            from consultation_analyser.consultations import ml_pipeline

            ml_pipeline.save_themes_for_consultation(consultation_id=consultation.id)
    # TODO - pass through messages - "themes created" or "consultation already has themes"
    context = {"consultation": consultation}
    return render(request, "support_console/consultation.html", context=context)
