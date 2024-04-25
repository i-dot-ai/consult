from django.contrib import messages
from django.contrib.auth import logout
from django.http import HttpRequest
from django.shortcuts import redirect, render
from magic_link.models import MagicLink
from waffle.decorators import waffle_switch

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations.forms.sessions import NewSessionForm
from consultation_analyser.email import send_magic_link_email


def get_magic_link_for_email(request: HttpRequest, email: str) -> str:
    try:
        user = User.objects.get(email=email)
        link = MagicLink.objects.create(user=user, redirect_to="/")
        return request.build_absolute_uri(link.get_absolute_url())
    except User.DoesNotExist:
        return ""


@waffle_switch("FRONTEND_USER_LOGIN")
def new(request: HttpRequest):
    if not request.POST:
        form = NewSessionForm()
    else:
        form = NewSessionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            magic_link = get_magic_link_for_email(request, email)
            send_magic_link_email(email, magic_link)
            return render(request, "magic_link/link_sent.html")

    return render(request, "new_session.html", {"form": form})


def destroy(request: HttpRequest):
    logout(request)
    messages.success(request, "You have signed out")
    return redirect("/")
