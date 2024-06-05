from uuid import UUID

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from consultation_analyser.consultations import models


@staff_member_required
def delete(request: HttpRequest, consultation_id: UUID, user_id: UUID) -> HttpResponse:
    consultation = models.Consultation.objects.get(id=consultation_id)
    user = models.User.objects.get(id=user_id)

    context = {
        "consultation": consultation,
        "user": user,
    }

    if request.POST:
        if "confirm_removal" in request.POST:
            consultation.users.remove(user)
            messages.success(request, f"{user.email} has been removed from this consultation")
            return redirect(
                reverse("support_consultation", kwargs={"consultation_id": consultation.id})
            )

    return render(request, "support_console/consultations_users/delete.html", context=context)
