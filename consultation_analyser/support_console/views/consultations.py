from uuid import UUID

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consultation_analyser.consultations import models
from consultation_analyser.consultations.download_consultation import consultation_to_json
from consultation_analyser.consultations.dummy_data import create_dummy_data
from consultation_analyser.hosting_environment import HostingEnvironment
from consultation_analyser.pipeline.backends.types import (
    NO_SUMMARY_STR,
)
from consultation_analyser.pipeline.processing import run_llm_summariser, run_processing_pipeline


@staff_member_required
def index(request: HttpRequest) -> HttpResponse:
    if request.POST:
        try:
            consultation = create_dummy_data()
            user = request.user
            consultation.users.add(user)
            messages.success(request, "A dummy consultation has been generated")
        except RuntimeError as error:
            messages.error(request, error.args[0])
    consultations = models.Consultation.objects.all()
    context = {"consultations": consultations, "production_env": HostingEnvironment.is_production()}
    return render(request, "support_console/consultations/index.html", context=context)


@staff_member_required
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


def get_number_themes_for_processing_run(consultation, processing_run=None):
    """
    Get total themes for processing run.
    If processing_run not specified, get the latest processing run if exists.
    """
    total_themes = 0
    total_with_summaries = 0
    if not consultation.has_processing_run():
        return total_themes, total_with_summaries
    if not processing_run:
        processing_run = consultation.latest_processing_run
    total_themes = processing_run.themes.count()
    total_with_summaries = (
        processing_run.themes.exclude(summary="").exclude(summary=NO_SUMMARY_STR).count()
    )
    return total_themes, total_with_summaries


@staff_member_required
def show(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    consultation = models.Consultation.objects.get(id=consultation_id)
    try:
        if "generate_themes" in request.POST:
            run_processing_pipeline(consultation)
            messages.success(request, "Consultation data has been sent for processing")
        elif "llm_summarisation" in request.POST:
            if not consultation.latest_processing_run:
                messages.error(request, "Cannot run LLM summarisation as no topics created")
            else:
                run_llm_summariser(consultation)
                messages.success(
                    request, "(Re-)running LLM summarisation on the latest processing run"
                )
        elif "download_json" in request.POST:
            consultation_json = consultation_to_json(consultation)
            response = HttpResponse(consultation_json, content_type="application/json")
            response["Content-Disposition"] = f"attachment; filename={consultation.slug}.json"
            return response

    except RuntimeError as error:
        messages.error(request, error.args[0])

    total_themes, total_with_summaries = get_number_themes_for_processing_run(
        consultation
    )  # latest run

    processing_runs = consultation.processingrun_set.all().order_by("created_at")

    context = {
        "consultation": consultation,
        "processing_runs": processing_runs,
        "users": consultation.users.all(),
        "total_themes": total_themes,
        "total_with_summaries": total_with_summaries,
    }
    return render(request, "support_console/consultations/show.html", context=context)
