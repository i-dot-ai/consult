from datetime import datetime
from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render

from .. import models
from .decorators import user_can_see_consultation, user_can_see_dashboards


@user_can_see_dashboards
@user_can_see_consultation
def index(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
):
    # Get question data
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(
        models.Question,
        slug=question_slug,
        consultation=consultation,
    )

    """Simplified index that just renders the template - all data loaded via AJAX"""
    # Minimal context - all dynamic data loaded via respondents_json
    context = {
        "consultation_name": consultation.title,
        "consultation_slug": consultation_slug,
        "question": question,
        "question_slug": question_slug,
        "free_text_question_part": question if question.has_free_text else None,
        "has_multiple_choice_question_part": question.has_multiple_choice,
        "selected_theme_mappings": [],  # Empty - loaded via AJAX
        "csv_button_data": [],  # Empty - loaded via AJAX
        "multiple_choice_summary": [],  # Empty - loaded via AJAX
        "stance_options": models.ResponseAnnotation.Sentiment.names,
        "has_individual_data": False,  # Shouldn't use this, demographic filters work more generally
    }

    return render(request, "consultations/answers/index.html", context)


@user_can_see_consultation
def show(
    request: HttpRequest,
    consultation_slug: str,
    question_slug: str,
    response_id: UUID,
):
    # Allow user to review and update theme mappings for a response.
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(models.Question, slug=question_slug, consultation=consultation)
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
            "show_next_response", consultation_slug=consultation_slug, question_slug=question_slug
        )

    elif request.method == "GET":
        context = {
            "consultation_name": consultation.title,
            "consultation_slug": consultation_slug,
            "question": question,
            "response": response,
            "all_themes": list(all_themes),
            "existing_themes": list(existing_themes),
            "date_created": datetime.strftime(response.created_at, "%d %B %Y"),
        }

        return render(request, "consultations/answers/show.html", context)


@user_can_see_consultation
def show_next(request: HttpRequest, consultation_slug: str, question_slug: str):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question = get_object_or_404(models.Question, slug=question_slug, consultation=consultation)

    def handle_no_responses():
        context = {
            "consultation_name": consultation.title,
            "consultation_slug": consultation_slug,
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
            consultation_slug=consultation_slug,
            question_slug=question_slug,
            response_id=next_response.id,
        )

    return handle_no_responses()