from uuid import UUID

from django.shortcuts import render

from .decorators import user_can_see_consultation


@user_can_see_consultation
def index(request, consultation_id: UUID):
    context = {
        "consultation_id": consultation_id,
    }
    return render(request, "consultations/questions/index.html", context)
