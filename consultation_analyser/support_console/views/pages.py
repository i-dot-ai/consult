from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.http import HttpRequest
from django.shortcuts import redirect, render


@staff_member_required
def sign_out(request: HttpRequest):
    logout(request)
    return redirect("/")
