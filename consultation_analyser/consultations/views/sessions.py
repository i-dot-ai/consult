from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import logout
from django.shortcuts import redirect

from consultation_analyser.authentication.models import User
from magic_link.models import MagicLink


def new(request: HttpRequest):
    if not request.POST:
        return render(request, "new_session.html")
    else:
        # TODO
        # do not 404 on invalid user as it's insecure
        # use a form for this
        user = get_object_or_404(User, email=request.POST.get("email", ""))
        link = MagicLink.objects.create(user=user, redirect_to="/")
        url = request.build_absolute_uri(link.get_absolute_url())
        return render(request, "magic_link/link_sent.html", {"link": url})


def destroy(request: HttpRequest):
    logout(request)
    return redirect("/")
