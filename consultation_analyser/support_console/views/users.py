from django.contrib import messages
from django.http import HttpRequest
from django.shortcuts import redirect, render, get_object_or_404

from consultation_analyser.authentication.models import User

from ..forms.new_user_form import NewUserForm


def index(request: HttpRequest):
    users = User.objects.all().order_by("-created_at")
    return render(request, "support_console/all-users.html", {"users": users})


def new(request: HttpRequest):
    if not request.POST:
        form = NewUserForm()
    else:
        form = NewUserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            User.objects.create_user(email=email)
            messages.success(request, "User added")
            return redirect("/support/users")

    return render(request, "support_console/new-user.html", {"form": form})



def show(request: HttpRequest, user_id: int):
    user = get_object_or_404(User, pk=user_id)
    consultations = user.consultation_set.all()
    return render(request, "support_console/user.html", {"user": user, "consultations": consultations})

