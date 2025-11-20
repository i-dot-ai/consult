from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest
from django.shortcuts import redirect


@login_not_required
def destroy(request: HttpRequest):
    logout(request)
    messages.success(request, "You have signed out")
    return redirect("/")
