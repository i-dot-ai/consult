from django.shortcuts import render

from .decorators import user_can_see_consultation


@user_can_see_consultation
def index(request, consultation_slug: str):
    context = {
        "consultation_slug": consultation_slug,
    }
    return render(request, "consultations/questions/index.html", context)
