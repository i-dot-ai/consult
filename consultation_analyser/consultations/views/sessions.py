from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest
from django.shortcuts import redirect


@login_not_required
def new(request: HttpRequest):
    """Redirect to OAuth login"""
    return redirect("/accounts/openid_connect/security_gov_uk/login/")


@login_not_required
def destroy(request: HttpRequest):
    """Sign out user and clear cookies"""
    logout(request)

    response = redirect("/")
    # Clear authentication cookies
    response.delete_cookie("access")
    response.delete_cookie("sessionId")

    messages.success(request, "You have signed out")
    return response
