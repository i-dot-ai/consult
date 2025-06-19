from django.shortcuts import get_object_or_404, render

from .. import models
from .decorators import user_can_see_consultation


@user_can_see_consultation
def index(request, consultation_slug: str):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)

    # Get questions that have free text and have themes
    questions_with_themes = models.Question.objects.filter(
        consultation=consultation, has_free_text=True, theme__isnull=False
    ).distinct()

    context = {
        "consultation": consultation,
        "question_parts": questions_with_themes,  # Using same variable name for template compatibility
    }
    return render(request, "consultations/questions/index.html", context)
