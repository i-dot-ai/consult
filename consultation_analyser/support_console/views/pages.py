from django.contrib.auth import logout
from django.http import HttpRequest
from django.shortcuts import redirect
from django.conf import settings

logger = settings.LOGGER


def sign_out(request: HttpRequest):
    logger.refresh_context()

    logout(request)
    return redirect("/")
