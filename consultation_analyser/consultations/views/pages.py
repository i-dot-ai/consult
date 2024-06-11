from django.http import HttpRequest
from django.shortcuts import render


def home(request: HttpRequest):
    return render(request, "static_pages/home.html")


def privacy(request: HttpRequest):
    return render(request, "static_pages/privacy.html")


def data_sharing(request: HttpRequest):
    return render(request, "static_pages/data_sharing.html")


def how_it_works(request: HttpRequest):
    return render(request, "static_pages/how_it_works.html")


def get_involved(request: HttpRequest):
    return render(request, "static_pages/get_involved.html")
