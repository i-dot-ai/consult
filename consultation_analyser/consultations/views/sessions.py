from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import logout
from django.shortcuts import redirect

from consultation_analyser.authentication.models import User
from magic_link.models import MagicLink

from consultation_analyser.consultations.forms.sessions import NewSessionForm


def get_magic_link_for_email(request: HttpRequest, email: str) -> str:
    try:
        user = User.objects.get(email=email)
        link = MagicLink.objects.create(user=user, redirect_to="/")
        return request.build_absolute_uri(link.get_absolute_url())
    except User.DoesNotExist:
        return ""


def new(request: HttpRequest):
    if not request.POST:
        form = NewSessionForm()
    else:
        form = NewSessionForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            url = get_magic_link_for_email(request, email)
            return render(request, "magic_link/link_sent.html", {"link": url})

    return render(request, "new_session.html", {"form": form})


def destroy(request: HttpRequest):
    logout(request)
    return redirect("/")
