from django.shortcuts import get_object_or_404, render

from .. import models
from .decorators import user_can_see_consultation


@user_can_see_consultation
def index(request, consultation_slug: str):
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    question_parts = models.QuestionPart.objects.filter(
        question__consultation=consultation, type=models.QuestionPart.QuestionType.FREE_TEXT
    )
    question_parts_with_themes = [
        q
        for q in question_parts
        if models.ThemeMapping.get_latest_theme_mappings(question_part=q).exists()
    ]
    context = {
        "consultation": consultation,
        "question_parts": question_parts_with_themes,
    }
    return render(request, "consultations/questions/index.html", context)
