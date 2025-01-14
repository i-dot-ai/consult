import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .. import models
from .decorators import user_can_see_consultation

logger = logging.getLogger("upload")


NO_THEMES_YET_MESSAGE = "We are processing your consultation. Themes have not been generated yet."


@login_required
def index(request: HttpRequest) -> HttpResponse:
    user = request.user
    consultations_for_user = models.Consultation.objects.filter(users=user)
    is_staff = user.is_staff
    context = {"consultations": consultations_for_user, "is_staff": is_staff}
    return render(request, "consultations/consultations/index.html", context)


@user_can_see_consultation
@login_required
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    questions = models.Question.objects.filter(consultation__slug=consultation_slug).order_by(
        "number"
    )
    context = {
        "questions": questions,
        "consultation": consultation,
    }
    # TODO - do something better if there is no question text, and get it from the question parts
    return render(request, "consultations/consultations/show.html", context)
