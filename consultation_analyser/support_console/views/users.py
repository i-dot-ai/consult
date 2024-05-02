from django.shortcuts import render
from django.http import HttpRequest

from consultation_analyser.authentication.models import User

def index(request: HttpRequest):
    users = User.objects.all()
    return render(request, "support_console/all-users.html", { "users": users })
