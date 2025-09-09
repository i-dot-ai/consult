from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from .. import models
from .decorators import user_can_see_consultation

logger = settings.LOGGER


@user_can_see_consultation
def show(
    request: HttpRequest,
    consultation_id: UUID,
    question_id: UUID,
    response_id: UUID,
):
    logger.refresh_context()

    # Allow user to review and update theme mappings for a response.
    consultation = get_object_or_404(models.Consultation, id=consultation_id)
    question = get_object_or_404(models.Question, id=question_id, consultation=consultation)
    response = get_object_or_404(models.Response, id=response_id, question=question)

    # Get or create annotation for this response
    annotation, _ = models.ResponseAnnotation.objects.get_or_create(response=response)

    # Get all themes for this question
    all_themes = models.Theme.objects.filter(question=question)

    # Get existing themes for this response
    existing_themes = annotation.themes.all().values_list("id", flat=True)

    if request.method == "POST":
        requested_themes = request.POST.getlist("theme")

        # Set human-reviewed themes (preserves original AI assignments)
        if requested_themes:
            themes_to_add = models.Theme.objects.filter(id__in=requested_themes, question=question)
            annotation.set_human_reviewed_themes(themes_to_add, request.user)
        else:
            # No themes selected - clear human-reviewed assignments
            annotation.set_human_reviewed_themes([], request.user)

        # Mark as human reviewed
        annotation.mark_human_reviewed(request.user)

        return redirect(
            "show_next_response", consultation_id=consultation_id, question_id=question_id
        )

    elif request.method == "GET":
        context = {
            "consultation_name": consultation.title,
            "consultation_id": consultation_id,
            "question": question,
            "response": response,
            "all_themes": list(all_themes),
            "existing_themes": list(existing_themes),
            "date_created": datetime.strftime(response.created_at, "%d %B %Y"),
        }

        return render(request, "consultations/answers/show.html", context)


@user_can_see_consultation
def show_next(request: HttpRequest, consultation_id: UUID, question_id: UUID):
    logger.refresh_context()
    consultation = get_object_or_404(models.Consultation, id=consultation_id)
    question = get_object_or_404(models.Question, id=question_id, consultation=consultation)

    def handle_no_responses():
        context = {
            "consultation_name": consultation.title,
            "consultation_slug": consultation.slug,
            "question": question,
        }
        return render(request, "consultations/answers/no_responses.html", context)

    # Check if this question has free text (only free text questions have themes)
    if not question.has_free_text:
        return handle_no_responses()

    # Get the next response that has not been human reviewed
    # Left join with annotation to find responses without annotations or not reviewed
    next_response = (
        models.Response.objects.filter(
            question=question,
            free_text__isnull=False,  # Only responses with free text
            free_text__gt="",  # Non-empty free text
        )
        .exclude(
            annotation__human_reviewed=True  # Exclude already reviewed
        )
        .order_by("?")
        .first()
    )

    if next_response:
        return redirect(
            "show_response",
            consultation_id=consultation_id,
            question_id=question_id,
            response_id=next_response.id,
        )

    return handle_no_responses()
