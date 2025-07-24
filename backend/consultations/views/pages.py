from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest
from django.shortcuts import render


@login_not_required
def home(request: HttpRequest):
    return render(request, "static_pages/home.html")


@login_not_required
def privacy(request: HttpRequest):
    return render(request, "static_pages/privacy.html")


@login_not_required
def data_sharing(request: HttpRequest):
    return render(request, "static_pages/data_sharing.html")


@login_not_required
def how_it_works(request: HttpRequest):
    return render(request, "static_pages/how_it_works.html")


@login_not_required
def get_involved(request: HttpRequest):
    return render(request, "static_pages/get_involved.html")
