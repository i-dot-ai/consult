from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.contrib.messages import get_messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consultation_analyser.consultations import dummy_data, ml_pipeline, models
from consultation_analyser.hosting_environment import HostingEnvironment


@staff_member_required
def support_home(request: HttpRequest):
    return render(request, "support_console/home.html")


@staff_member_required
def sign_out(request: HttpRequest):
    logout(request)
    return redirect("/")


@staff_member_required
def ml_pipeline_test(request: HttpRequest) -> HttpResponse:
    if request.POST:
        if "generate_dummy_consultation" in request.POST:
            try:
                dummy_data.DummyConsultation(include_themes=False)
                messages.add_message(request, messages.INFO, "New consultation generated")
            except RuntimeError as error:
                messages.add_message(request, messages.WARN, error.args[0])
        else:
            consultation_id = request.POST.get("consultation_id")
            themes_already_exist = models.Theme.objects.filter(
                answer__question__section__consultation__id=consultation_id
            ).exists()
            if not themes_already_exist:
                ml_pipeline.save_themes_for_consultation(consultation_id=consultation_id)
                messages.add_message(request, messages.INFO, "Themes created for consultation")
            else:
                messages.add_message(request, messages.INFO, "Themes already exist for this consultation")

    # TODO - messages
    consultations = models.Consultation.objects.all()

    context = {"consultations": consultations, "messages": get_messages(request)}
    return render(request, "support_console/ml_pipeline_test.html", context=context)


@staff_member_required
def show_consultations(request: HttpRequest) -> HttpResponse:
    if request.POST:
        try:
            dummy_data.DummyConsultation(include_themes=False)
            messages.add_message(request, messages.INFO, "New consultation generated")
        except RuntimeError as error:
            messages.add_message(request, messages.WARNING, error.args[0])
    consultations = models.Consultation.objects.all()
    # TODO - do something with messages
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
            ml_pipeline.save_themes_for_consultation(consultation_id=consultation.id)
            messages.add_message(request, messages.INFO, "Themes created for consultation")
        else:
            messages.add_message(request, messages.INFO, "Themes already exist for this consultation")
    # TODO - do something with messages
    context = {"consultation": consultation}
    return render(request, "support_console/consultation.html", context=context)
