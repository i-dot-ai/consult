from django.contrib import messages
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render


def show(request: HttpRequest) -> HttpResponse:
    if request.POST:
        return redirect("cache-delete-confirmation")
    return render(request, "support_console/cache/show.html")


def delete(request: HttpRequest) -> HttpResponse:
    if request.POST:
        if "confirm_deletion" in request.POST:
            # Note this clears the default cache only
            cache.clear()
            messages.success(request, "The default cache has been deleted")
            return redirect("support")
    return render(request, "support_console/cache/delete.html")
