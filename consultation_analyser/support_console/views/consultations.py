from uuid import UUID

from django.contrib import messages
from django.core.management import call_command
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consultation_analyser.consultations import models
from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml
from consultation_analyser.hosting_environment import HostingEnvironment

NO_SUMMARY_STR = "Unable to generate summary for this theme"


def index(request: HttpRequest) -> HttpResponse:
    if request.POST:
        try:
            consultation = create_dummy_consultation_from_yaml()
            user = request.user
            consultation.users.add(user)
            messages.success(request, "A dummy consultation has been generated")
        except RuntimeError as error:
            messages.error(request, error.args[0])
    consultations = models.Consultation.objects.all()
    context = {"consultations": consultations, "production_env": HostingEnvironment.is_production()}
    return render(request, "support_console/consultations/index.html", context=context)


def delete(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    consultation = models.Consultation.objects.get(id=consultation_id)
    context = {
        "consultation": consultation,
    }

    if request.POST:
        if "confirm_deletion" in request.POST:
            consultation.delete()
            messages.success(request, "The consultation has been deleted")
            return redirect("/support/consultations/")

    return render(request, "support_console/consultations/delete.html", context=context)


def get_number_themes_for_processing_run(processing_run):
    """
    Get total themes for processing run.
    If processing_run not specified, get the latest processing run if exists.
    """
    if not processing_run:
        return 0, 0
    total_themes = processing_run.themes.count()
    total_with_summaries = (
        processing_run.themes.exclude(summary="").exclude(summary=NO_SUMMARY_STR).count()
    )
    return total_themes, total_with_summaries


def show(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    consultation = models.Consultation.objects.get(id=consultation_id)

    context = {
        "consultation": consultation,
        "users": consultation.users.all(),
    }
    return render(request, "support_console/consultations/show.html", context=context)


def import_consultations(request: HttpRequest) -> HttpResponse:
    if request.POST:
        s3_key = request.POST.get("s3_key")
        call_command("import_consultation_data", s3_key)
        messages.success(request, "Consultations imported")

        return redirect("/support/consultations/")
    return render(request, "support_console/consultations/import.html")
