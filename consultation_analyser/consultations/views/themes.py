from typing import Optional
from uuid import UUID

from django.conf import settings
from django.shortcuts import get_object_or_404, render

from ..models import Question
from .decorators import user_can_see_consultation

logger = settings.LOGGER


@user_can_see_consultation
def theme_list(request, consultation_id: UUID, question_id: UUID):
    """List all themes for a question - data loaded via API"""
    logger.refresh_context()
    question = get_object_or_404(Question, id=question_id, consultation_id=consultation_id)

    context = {
        "consultation_id": consultation_id,
        "question_id": question_id,
        "question": question,
    }
    return render(request, "consultations/questions/themes.html", context)


@user_can_see_consultation
def theme_detail(request, consultation_id: UUID, question_id: UUID, theme_id: Optional[UUID] = None):
    """Add new theme or edit existing theme - CRUD operations via API"""
    logger.refresh_context()

    context = {
        "consultation_id": consultation_id,
        "question_id": question_id,
        "theme_id": theme_id,
    }
    return render(request, "consultations/questions/theme_detail.html", context)
