from django.http import HttpRequest
from django.shortcuts import render
from waffle.decorators import waffle_switch

from consultation_analyser.batch_calls import BatchJobHandler
from consultation_analyser.hosting_environment import HostingEnvironment

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


# TODO - simple view for testing batch jobs
# To be removed once tested
@waffle_switch("CONSULTATION_PROCESSING")
def batch_example(request: HttpRequest):
    message = ""
    if request.POST:
        job_name = "batch_example"
        command = {"command": ["venv/bin/django-admin", "basic_management_command"]}
        if not HostingEnvironment.is_local():
            batch_handler = BatchJobHandler()
            batch_handler.submit_job_batch(jobName=job_name, containerOverrides=command)
            message = "Batch job has been run"
        else:
            message = "Batch job not run locally"
    context = {"message": message}
    return render(request, "batch_example.html", context)
