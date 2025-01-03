import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .. import models
from .decorators import user_can_see_consultation

logger = logging.getLogger("upload")


NO_THEMES_YET_MESSAGE = "We are processing your consultation. Themes have not been generated yet."


@login_required
def index(request: HttpRequest) -> HttpResponse:
    user = request.user
    consultations_for_user = models.Consultation2.objects.filter(users=user)
    is_staff = user.is_staff
    context = {"consultations": consultations_for_user, "is_staff": is_staff}
    return render(request, "consultations/consultations/index.html", context)


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    consultation = get_object_or_404(models.Consultation2, slug=consultation_slug)
    questions = models.Question2.objects.filter(consultation__slug=consultation_slug).order_by(
        "order"
    )
    context = {
        "questions": questions,
        "consultation": consultation,
    }
    # TODO - do something better if there is no question text, and get it from the question parts
    return render(request, "consultations/consultations/show.html", context)
<<<<<<< HEAD
=======


# TODO - to be removed (separate PR?)
@login_required
def new(request: HttpRequest):
    if not request.POST:
        form = ConsultationUploadForm()
    else:
        logger.info("Upload received")
        form = ConsultationUploadForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info("Enqueueing upload_consultation job")
            file_path = storage.save(
                request.FILES["consultation_json"].name, request.FILES["consultation_json"]
            )
            async_upload_consultation.delay(file_path, request.user.id)
            return render(request, "consultations/consultations/uploaded.html", {})

    return render(request, "consultations/consultations/new.html", {"form": form})
>>>>>>> 93526a0 (Change consultation views to use new consultation model.)
