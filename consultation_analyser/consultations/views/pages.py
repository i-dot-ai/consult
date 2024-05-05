from django.http import HttpRequest
from django.shortcuts import render
from waffle.decorators import waffle_switch

from consultation_analyser.hosting_environment import HostingEnvironment
from consultation_analyser.pipeline.batch_calls import BatchJobHandler

from .. import models


def home(request: HttpRequest):
    return render(request, "home.html")


def privacy(request: HttpRequest):
    return render(request, "privacy.html")


def data_sharing(request: HttpRequest):
    return render(request, "data_sharing.html")


def how_it_works(request: HttpRequest):
    return render(request, "how_it_works.html")


def get_involved(request: HttpRequest):
    return render(request, "get_involved.html")
