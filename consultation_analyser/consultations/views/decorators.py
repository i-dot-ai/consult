from django.shortcuts import get_object_or_404

from .. import models


def user_can_see_consultation(view_function):
    def decorator(request, *args, **kwargs):
        slug = kwargs.get("consultation_slug")

        # will kick out users by throwing a 404 if they don't own the consultation
        get_object_or_404(models.Consultation.objects.filter(slug=slug, users__in=[request.user]))

        return view_function(request, *args, **kwargs)

    return decorator
