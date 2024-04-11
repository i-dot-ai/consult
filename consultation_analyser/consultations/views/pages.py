from django.http import HttpRequest
from django.shortcuts import render

from consultation_analyser.batch_calls import BatchJobHandler
from consultation_analyser.hosting_environment import HostingEnvironment

from .. import models


def home(request: HttpRequest):
    questions = models.Question.objects.all().order_by("id")[:10]
    context = {"questions": questions}
    return render(request, "home.html", context)


def privacy(request: HttpRequest):
    return render(request, "privacy.html")


# TODO - simple view for testing batch jobs
# To be removed once tested
def batch_example(request: HttpRequest):
    message = ""
    if request.POST:
        # TODO - run management command
        job_name = "batch_example"
        command = {"command": ["python", "manage.py", "basic_management_command"]}
        if not HostingEnvironment.is_local():
            batch_handler = BatchJobHandler()
            batch_handler.submit_job_batch(jobName=job_name, containerOverrides=command)
            message = "Batch job has been run"
        else:
            message = "Batch job not run locally"
    context = {"message": message}
    return render(request, "batch_example.html", context)
