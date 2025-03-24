import logging
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.core.management import call_command
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from consultation_analyser.consultations import models
from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml
from consultation_analyser.consultations.export_user_theme import export_user_theme_job
from consultation_analyser.hosting_environment import HostingEnvironment
from consultation_analyser.support_console.export_url_guidance import get_urls_for_consultation
from consultation_analyser.support_console.ingest import import_themefinder_data_for_question_job

logger = logging.getLogger("export")


def index(request: HttpRequest) -> HttpResponse:
    if request.POST:
        try:
            if request.POST.get("generate_dummy_consultation") is not None:
                consultation = create_dummy_consultation_from_yaml()
                user = request.user
                consultation.users.add(user)
                messages.success(request, "A dummy consultation has been generated")
            elif request.POST.get("create_synthetic_consultation") is not None:
                call_command("import_synthetic_data")
                messages.success(request, "Synthetic data imported")
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


def show(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    consultation = models.Consultation.objects.get(id=consultation_id)

    context = {
        "consultation": consultation,
        "users": consultation.users.all(),
    }
    return render(request, "support_console/consultations/show.html", context=context)


def import_consultations_xlsx(request: HttpRequest) -> HttpResponse:
    if request.POST:
        s3_key = request.POST.get("s3_key")
        call_command("import_consultation_data", s3_key)
        messages.success(request, "Consultations imported")

        return redirect("/support/consultations/")
    return render(request, "support_console/consultations/import_xlsx.html")


def export_consultation_theme_audit(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    consultation = get_object_or_404(models.Consultation, id=consultation_id)

    context = {
        "consultation": consultation,
        "bucket_name": settings.AWS_BUCKET_NAME,
        "environment": settings.ENVIRONMENT,
    }

    if request.method == "POST":
        s3_key = request.POST.get("s3_key", "")
        try:
            logging.info("Exporting theme audit data - sending to queue")
            export_user_theme_job.delay(consultation.slug, s3_key)
        except Exception as e:
            messages.error(request, e)
            return render(request, "support_console/consultations/export_audit.html", context)

        messages.success(request, "Consultation theme audit export started")
        return redirect("/support/consultations/")

    return render(request, "support_console/consultations/export_audit.html", context)


def import_theme_mapping(request: HttpRequest) -> HttpResponse:
    current_user = request.user
    if request.POST:
        consultation_slug = request.POST.get("consultation_slug")
        consultation_name = request.POST.get("consultation_name")
        path_to_outputs = request.POST.get("path")
        if consultation_slug:
            consultation = models.Consultation.objects.get(slug=consultation_slug)
            if consultation_name:
                consultation.title = consultation_name
                consultation.save()
        else:
            if not consultation_name:
                consultation_name = "New Consultation"
            consultation = models.Consultation.objects.create(title=consultation_name)
        consultation.users.add(current_user)
        consultation.save()

        question_numbers = models.Question.objects.filter(consultation=consultation).values_list(
            "number", flat=True
        )
        max_existing = max(question_numbers) if question_numbers else 0
        next_question_number = max_existing + 1
        import_themefinder_data_for_question_job.delay(
            consultation=consultation,
            question_number=next_question_number,
            question_folder=path_to_outputs,
        )
        return redirect("/support/consultations/")
    context = {"bucket_name": settings.AWS_BUCKET_NAME}
    return render(request, "support_console/consultations/import.html", context=context)


def export_urls_for_consultation(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    context = {"bucket_name": settings.AWS_BUCKET_NAME}

    if request.method == "POST":
        s3_key = request.POST.get("s3_key")
        filename = request.POST.get("filename")

        try:
            consultation = get_object_or_404(models.Consultation, id=consultation_id)
            base_url = request.build_absolute_uri("/")
            get_urls_for_consultation(consultation, base_url, s3_key, filename)

            messages.success(
                request, f"Consultation URLs exported to {settings.AWS_BUCKET_NAME}/{s3_key}"
            )
            return redirect("/support/consultations/")
        except Exception as e:
            messages.error(request, e)
            return render(request, "support_console/consultations/export_urls.html", context)

    return render(request, "support_console/consultations/export_urls.html", context)
