from django.contrib import messages
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django_rq import job


@job("default", timeout=900)
def delete_cache_job():
    cache.clear()


def show(request: HttpRequest) -> HttpResponse:
    if request.POST:
        return redirect("cache-delete-confirmation")
    return render(request, "support_console/cache/show.html")


def delete(request: HttpRequest) -> HttpResponse:
    if request.POST:
        if "confirm_deletion" in request.POST:
            delete_cache_job.delay()
            messages.success(
                request,
                "The consultation has been sent for deletion - check queue dashboard for progress",
            )
            return redirect("support")
    return render(request, "support_console/cache/delete.html")
