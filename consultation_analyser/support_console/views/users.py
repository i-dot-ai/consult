from django.contrib import messages
from django.contrib.auth.models import Group
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from consultation_analyser.authentication.models import User
from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.models import Consultation

from ..forms.edit_user_form import EditUserForm
from ..forms.new_user_form import NewUserForm


def index(request: HttpRequest):
    users = User.objects.all().order_by("email")
    return render(request, "support_console/users/index.html", {"users": users})


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

    return render(request, "support_console/users/new.html", {"form": form})


def show(request: HttpRequest, user_id: int):
    user = get_object_or_404(User, pk=user_id)
    consultations = Consultation.objects.filter(users__in=[user])
    dashboard_group = Group.objects.get(name=DASHBOARD_ACCESS)
    user_currently_has_dashboard_access = dashboard_group in user.groups.all()

    if not request.POST:
        form = EditUserForm(
            {
                "user_id": user_id,
                "is_staff": user.is_staff,
                "dashboard_access": user_currently_has_dashboard_access,
            }
        )
    else:
        form = EditUserForm(request.POST, current_user=request.user)
        if form.is_valid():
            is_staff = form.cleaned_data["is_staff"]
            user.is_staff = is_staff
            user.save()

            assign_dashboard_access = form.cleaned_data["dashboard_access"]
            if assign_dashboard_access:
                user.groups.add(dashboard_group)
                user.save()

            elif user_currently_has_dashboard_access:
                user.groups.remove(dashboard_group)
                user.save()

            messages.success(request, "User updated")
            return redirect(request.path_info)

    return render(
        request,
        "support_console/users/show.html",
        {"user": user, "consultations": consultations, "form": form},
    )
