import logging

import magic_link.views
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from magic_link.models import MagicLink

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations.forms.sessions import NewSessionForm
from consultation_analyser.email import send_magic_link_email
from consultation_analyser.hosting_environment import HostingEnvironment


def send_magic_link_if_email_exists(request: HttpRequest, email: str) -> None:
    try:
        email = email.lower()
        user = User.objects.get(email=email)
        link = MagicLink.objects.create(user=user, redirect_to="/")
        magic_link = request.build_absolute_uri(link.get_absolute_url())
        # Log magic link in local environment only
        if HostingEnvironment.is_local():
            logger = logging.getLogger("django.server")
            logger.info(f"##################### Sending magic link to {email}: {magic_link}")

        # Send email in test and deployed environments (test backend will capture it)
        # Use Django's test detection as fallback
        is_test_environment = HostingEnvironment.is_test() or "test" in settings.SETTINGS_MODULE
        if not HostingEnvironment.is_local() or is_test_environment:
            send_magic_link_email(email, magic_link)
    except User.DoesNotExist:
        pass


@login_not_required
def new(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("/")

    if not request.POST:
        form = NewSessionForm()
    else:
        form = NewSessionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            send_magic_link_if_email_exists(request, email)
            return render(request, "magic_link/link_sent.html")

    return render(request, "consultations/sessions/new.html", {"form": form})


@login_not_required
def destroy(request: HttpRequest):
    logout(request)
    messages.success(request, "You have signed out")
    return redirect("/")


@method_decorator(login_not_required, name="dispatch")
class MagicLinkView(magic_link.views.MagicLinkView):
    pass
