from uuid import UUID

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consultation_analyser.consultations import models


def delete(request: HttpRequest, consultation_id: UUID, question_id: UUID) -> HttpResponse:
    question = models.Question.objects.get(consultation__id=consultation_id, id=question_id)
    context = {
        "question": question,
    }

    if request.POST:
        if "confirm_deletion" in request.POST:
            question.delete()
            messages.success(request, "The question has been deleted")
            return redirect("/support/consultations/")
        else:
            return redirect(f"/support/consultations/{consultation_id}/")
    return render(request, "support_console/questions/delete.html", context=context)
