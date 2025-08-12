from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .decorators import user_can_see_consultation, user_can_see_dashboards


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "consultations/consultations/index.html")


@user_can_see_dashboards
@user_can_see_consultation
def show(request: HttpRequest, consultation_id: UUID) -> HttpResponse:
    # Dashboard page - pass consultation_slug to template for API calls
    context = {
        "consultation_id": consultation_id,
    }
    return render(request, "consultations/consultations/show.html", context)
