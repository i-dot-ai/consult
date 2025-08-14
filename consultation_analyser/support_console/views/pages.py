from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpRequest
from django.shortcuts import redirect

logger = settings.LOGGER


def sign_out(request: HttpRequest):
    logger.refresh_context()

    logout(request)
    return redirect("/")
