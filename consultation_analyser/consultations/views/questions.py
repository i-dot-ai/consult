import json
from uuid import UUID

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from ..models import Question, Theme
from .decorators import user_can_see_consultation

logger = settings.LOGGER


@user_can_see_consultation
def index(request, consultation_id: UUID):
    logger.refresh_context()
    context = {
        "consultation_id": consultation_id,
    }
    return render(request, "consultations/questions/index.html", context)


@user_can_see_consultation
def annotate(request, consultation_id: UUID, question_id: UUID):
    logger.refresh_context()
    question = get_object_or_404(Question, id=question_id, consultation_id=consultation_id)

    if request.method == "POST":
        try:
            # Get the themes JSON data
            themes_json = request.POST.get("themes", "[]")
            themes = json.loads(themes_json)

            # Clear existing themes for this question first (complete replacement)
            Theme.objects.filter(question=question).delete()

            # Process each theme and save to database
            saved_themes = []
            for theme in themes:
                name = theme.get("name", "").strip()
                description = theme.get("description", "").strip()

                # Only save non-empty themes
                if name or description:
                    # Create new theme in database
                    theme_obj = Theme.objects.create(
                        question=question, name=name, description=description
                    )

                    theme_data = {"id": str(theme_obj.id), "name": name, "description": description}
                    saved_themes.append(theme_data)

            logger.info(f"Saved {len(saved_themes)} themes for question {question_id}")

            message = f"Successfully saved {len(saved_themes)} theme{'s' if len(saved_themes) != 1 else ''}"
            return JsonResponse(
                {"status": "success", "message": message, "themes_count": len(saved_themes)}
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid theme data format"}, status=400
            )
        except Exception as e:
            logger.error(f"Error saving themes: {str(e)}")
            return JsonResponse({"status": "error", "message": "Failed to save themes"}, status=500)

    # Get existing themes for this question
    existing_themes = Theme.objects.filter(question=question).values("name", "description")

    context = {
        "consultation_id": consultation_id,
        "question_id": question_id,
        "question": question,
        "existing_themes": list(existing_themes),
    }
    return render(request, "consultations/questions/annotate.html", context)
