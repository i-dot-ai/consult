import logging
from typing import Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .. import models
from .decorators import user_can_see_consultation

logger = logging.getLogger("upload")


NO_THEMES_YET_MESSAGE = "We are processing your consultation. Themes have not been generated yet."


def index(request: HttpRequest) -> HttpResponse:
    consultations = request.user.consultation_set.all()
    user = request.user
    is_staff = user.is_staff
    context = {"consultations": consultations, "is_staff": is_staff}
    return render(request, "consultations/consultations/index.html", context)


@user_can_see_consultation
def show(
    request: HttpRequest, consultation_slug: str, processing_run_slug: Optional[str] = None
) -> HttpResponse:
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    try:
        processing_run = consultation.get_processing_run(processing_run_slug)
    except models.ProcessingRun.DoesNotExist:
        return Http404
    if not processing_run:
        messages.info(request, NO_THEMES_YET_MESSAGE)

    questions = models.Question.objects.filter(section__consultation__slug=consultation_slug)
    context = {
        "questions": questions,
        "consultation": consultation,
        "processing_run": processing_run,
    }

    return render(request, "consultations/consultations/show.html", context)
