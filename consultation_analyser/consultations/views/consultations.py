from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404

from .decorators import user_can_see_consultation, user_can_see_dashboards
from ..models import Consultation


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "consultations/consultations/index.html")


@user_can_see_dashboards
@user_can_see_consultation
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    # Dashboard page - pass consultation_slug to template for API calls
    consultation = get_object_or_404(Consultation, slug=consultation_slug)
    context = {
        "consultation_id": consultation.pk,
    }
    return render(request, "consultations/consultations/show.html", context)
