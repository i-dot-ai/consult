import logging
import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django_rq import get_queue, enqueue
from django.http import JsonResponse
from ..tasks import enqueue_job
from channels.layers import get_channel_layer


from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.consultations.upload_file import upload_file
from asgiref.sync import async_to_sync

from .. import models
from ..forms.consultation_upload_form import ConsultationUploadForm
from .decorators import user_can_see_consultation

logger = logging.getLogger("upload")


NO_THEMES_YET_MESSAGE = "We are processing your consultation. Themes have not been generated yet."


@login_required
def index(request: HttpRequest) -> HttpResponse:
    consultations = request.user.consultation_set.all()
    user = request.user
    is_staff = user.is_staff
    context = {"consultations": consultations, "is_staff": is_staff}
    return render(request, "consultations/consultations/index.html", context)


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug)
    context = {"questions": questions, "consultation": consultation}

    if not consultation.has_processing_run():
        messages.info(request, NO_THEMES_YET_MESSAGE)

    return render(request, "consultations/consultations/show.html", context)


@login_required
def new(request: HttpRequest):
    if not request.POST:
        form = ConsultationUploadForm()
    else:
        stime = time.time()
        logger.info("Upload received")
        form = ConsultationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info("Running upload_consultation")
            file_name = upload_file(request.FILES["consultation_json"])
            etime = time.time()
            logger.info(f"Total upload time: {etime - stime}s")

            job = enqueue_job(file_name, request.user)
            messages.success(request, f"The consultation has been uploaded to {job}")
           
            return render(request, "consultations/consultations/uploaded.html", {})

    return render(request, "consultations/consultations/new.html", {"form": form})

