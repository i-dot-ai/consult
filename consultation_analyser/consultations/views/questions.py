from django.shortcuts import render

from .decorators import user_can_see_consultation
from django.conf import settings

logger = settings.LOGGER


@user_can_see_consultation
def index(request, consultation_slug: str):
    logger.refresh_context()

    context = {
        "consultation_slug": consultation_slug,
    }
    return render(request, "consultations/questions/index.html", context)
