from django.http import HttpRequest
from django.shortcuts import redirect, reverse

from .pages import home


def root(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect(reverse("consultations"))
    else:
        return home(request)
