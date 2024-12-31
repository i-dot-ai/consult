from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest
from django.shortcuts import redirect, reverse

from .pages import home


@login_not_required
def root(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect(reverse("consultations"))
    else:
        return home(request)
