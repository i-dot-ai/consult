from typing import Optional
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Question, Theme
from .decorators import user_can_see_consultation

logger = settings.LOGGER


@user_can_see_consultation
def theme_list(request, consultation_id: UUID, question_id: UUID):
    """List all themes for a question"""
    logger.refresh_context()
    question = get_object_or_404(Question, id=question_id, consultation_id=consultation_id)
    themes = Theme.objects.filter(question=question).order_by("created_at")

    context = {
        "consultation_id": consultation_id,
        "question_id": question_id,
        "question": question,
        "themes": themes,
    }
    return render(request, "consultations/questions/themes.html", context)


@user_can_see_consultation
def theme_detail(
    request, consultation_id: UUID, question_id: UUID, theme_id: Optional[UUID] = None
):
    """Add new theme or edit existing theme"""
    logger.refresh_context()
    question = get_object_or_404(Question, id=question_id, consultation_id=consultation_id)

    # Get existing theme if editing
    theme = None
    if theme_id:
        theme = get_object_or_404(Theme, id=theme_id, question=question)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        # Basic validation
        if not name:
            messages.error(request, "Theme name is required.")
        else:
            try:
                if theme:
                    # Update existing theme
                    theme.name = name
                    theme.description = description
                    theme.save()
                    messages.success(request, "Theme updated successfully.")
                else:
                    # Create new theme
                    Theme.objects.create(question=question, name=name, description=description)
                    messages.success(request, "Theme created successfully.")

                # Redirect back to theme list
                return redirect(
                    "theme_list", consultation_id=consultation_id, question_id=question_id
                )

            except Exception as e:
                logger.error(f"Error saving theme: {str(e)}")
                messages.error(request, "Failed to save theme. Please try again.")

    context = {
        "consultation_id": consultation_id,
        "question_id": question_id,
        "question": question,
        "theme": theme,
    }
    return render(request, "consultations/questions/theme_detail.html", context)


@user_can_see_consultation
def theme_delete(request, consultation_id: UUID, question_id: UUID, theme_id: UUID):
    """Delete a theme"""
    logger.refresh_context()
    question = get_object_or_404(Question, id=question_id, consultation_id=consultation_id)
    theme = get_object_or_404(Theme, id=theme_id, question=question)

    if request.method == "POST":
        try:
            theme_name = theme.name
            theme.delete()
            messages.success(request, f"Theme '{theme_name}' deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting theme: {str(e)}")
            messages.error(request, "Failed to delete theme. Please try again.")

    return redirect("theme_list", consultation_id=consultation_id, question_id=question_id)
