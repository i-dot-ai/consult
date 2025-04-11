from uuid import UUID

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from consultation_analyser.consultations import models


def delete(request: HttpRequest, consultation_id: UUID, question_part_id: UUID) -> HttpResponse:
    question_part = models.QuestionPart.objects.get(
        question__consultation__id=consultation_id, id=question_part_id
    )
    context = {
        "question_part": question_part,
    }

    if request.POST:
        if "confirm_deletion" in request.POST:
            question_part.delete()
            messages.success(request, "The question part has been deleted")
            return redirect("/support/consultations/")
        else:
            return redirect(f"/support/consultations/{consultation_id}/")
    return render(request, "support_console/question_parts/delete.html", context=context)
