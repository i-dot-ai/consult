from django.shortcuts import render, redirect

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout
from django.http import HttpRequest


@staff_member_required
def support_home(request: HttpRequest):
    return render(request, "support_console/home.html")

@staff_member_required
def sign_out(request: HttpRequest):
    logout(request)
    return redirect('/')
