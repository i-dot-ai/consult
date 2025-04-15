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
from consultation_analyser.support_console.ingest import (
    get_all_question_part_subfolders,
    get_folder_names_for_dropdown,
    import_all_respondents_from_jsonl,
    import_all_responses_from_jsonl,
    import_all_sentiment_mappings_from_jsonl,
    import_all_theme_mappings_from_jsonl,
    import_question_part,
    import_themes_from_json,
)

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
    question_parts = models.QuestionPart.objects.filter(
        question__consultation=consultation
    ).order_by("question__number", "number")

    context = {
        "consultation": consultation,
        "users": consultation.users.all(),
        "question_parts": question_parts,
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


def import_consultation_respondents(request: HttpRequest) -> HttpResponse:
    current_user = request.user
    bucket_name = settings.AWS_BUCKET_NAME
    batch_size = 100

    consultation_folders = get_folder_names_for_dropdown()

    if request.POST:
        consultation_name = request.POST.get("consultation_name")
        consultation_code = request.POST.get("consultation_code")
        if not consultation_name:
            consultation_name = "New Consultation"
        consultation = models.Consultation.objects.create(title=consultation_name)
        consultation.users.add(current_user)
        consultation.save()
        input_folder_name = f"app_data/{consultation_code}/inputs/"
        import_all_respondents_from_jsonl(
            consultation=consultation,
            bucket_name=bucket_name,
            inputs_folder_key=input_folder_name,
            batch_size=batch_size,
        )
        msg = f"Importing respondents started for consultation with slug {consultation.slug} - check for progress in dashboard"
        messages.success(request, msg)
        return redirect("/support/consultations/import-summary/")
    context = {"bucket_name": bucket_name, "consultation_folders": consultation_folders}
    return render(request, "support_console/consultations/import_respondents.html", context=context)


def import_consultation_inputs(request: HttpRequest) -> HttpResponse:
    # Inputs are question text and responses, no themefinder outputs.
    # Respondents should already have been imported
    bucket_name = settings.AWS_BUCKET_NAME
    batch_size = 100

    all_consultations = models.Consultation.objects.all().order_by("-created_at")
    consultations_for_select = all_consultations.values("id", "title")
    consultations_for_select = [
        {"text": f"{d['title']} ({d['id']})", "value": d["id"]} for d in consultations_for_select
    ]

    consultation_folders = get_folder_names_for_dropdown()

    if request.POST:
        consultation_id = request.POST.get("consultation_id")
        consultation_code = request.POST.get("consultation_code")
        path_to_inputs = f"app_data/{consultation_code}/inputs/"

        consultation = models.Consultation.objects.get(id=consultation_id)
        question_part_subfolders = get_all_question_part_subfolders(
            folder_name=path_to_inputs, bucket_name=bucket_name
        )
        for folder in question_part_subfolders:
            question_part = import_question_part(
                consultation=consultation, question_part_folder_key=folder
            )
            import_all_responses_from_jsonl(
                question_part=question_part,
                bucket_name=bucket_name,
                question_part_folder_key=folder,
                batch_size=batch_size,
            )
        msg = f"Import for consultation inputs started for consultation with slug {consultation.slug} - check for progress in dashboard"
        messages.success(request, msg)
        return redirect("/support/consultations/import-summary/")
    context = {
        "bucket_name": bucket_name,
        "consultations_for_select": consultations_for_select,
        "consultation_folders": consultation_folders,
    }
    return render(request, "support_console/consultations/import_inputs.html", context=context)


def import_consultation_themes(request: HttpRequest) -> HttpResponse:
    # Imports themefinder outputs: themes, theme mappings and sentiment mappings
    # Responses should already have been imported
    bucket_name = settings.AWS_BUCKET_NAME
    consultation_options = [
        {"value": c.slug, "text": c.slug} for c in models.Consultation.objects.all()
    ]
    consultation_folders = get_folder_names_for_dropdown()
    context = {
        "consultations": consultation_options,
        "bucket_name": bucket_name,
        "consultation_folders": consultation_folders,
    }
    batch_size = 100

    if request.POST:
        consultation_slug = request.POST.get("consultation_slug")
        consultation_code = request.POST.get("consultation_code")
        consultation_mapping_date = request.POST.get("consultation_mapping_date")
        path_to_themes = f"app_data/{consultation_code}/outputs/mapping/{consultation_mapping_date}"

        consultation = models.Consultation.objects.get(slug=consultation_slug)
        if not models.Question.objects.filter(consultation=consultation).exists():
            messages.error(request, "Questions have not yet been imported for this Consultation")
            return render(
                request, "support_console/consultations/import_themes.html", context=context
            )

        question_part_subfolders = get_all_question_part_subfolders(
            folder_name=path_to_themes, bucket_name=bucket_name
        )

        for folder in question_part_subfolders:
            question_number = int(folder.split("/")[-2].split("question_part_")[-1])
            question_part = models.QuestionPart.objects.get(
                question__consultation=consultation,
                question__number=question_number,
                type=models.QuestionPart.QuestionType.FREE_TEXT,
            )

            import_themes_from_json(
                question_part=question_part,
                bucket_name=bucket_name,
                question_part_folder_key=folder,
            )
            import_all_theme_mappings_from_jsonl(
                question_part=question_part,
                bucket_name=bucket_name,
                question_part_folder_key=folder,
                batch_size=batch_size,
            )
            import_all_sentiment_mappings_from_jsonl(
                question_part=question_part,
                bucket_name=bucket_name,
                question_part_folder_key=folder,
                batch_size=batch_size,
            )

        msg = f"Importing themefinder outputs started for consultation with slug {consultation.slug} - check for progress in dashboard"
        messages.success(request, msg)
        return redirect("/support/consultations/import-summary/")

    return render(request, "support_console/consultations/import_themes.html", context=context)


def import_summary(request: HttpRequest) -> HttpResponse:
    return render(request, "support_console/consultations/import_summary.html", context={})
