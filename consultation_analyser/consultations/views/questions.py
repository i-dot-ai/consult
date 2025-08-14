from uuid import UUID

from django.conf import settings
from django.shortcuts import render

from .decorators import user_can_see_consultation

logger = settings.LOGGER


@user_can_see_consultation
def index(request, consultation_id: UUID):
    logger.refresh_context()
    context = {
        "consultation_id": consultation_id,
    }
    return render(request, "consultations/questions/index.html", context)
