from django.shortcuts import render

# from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest


def support_home(request: HttpRequest):
    return render(request, "support_console/home.html")
