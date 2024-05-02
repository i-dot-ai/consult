from django.shortcuts import get_object_or_404

from .. import models


def user_can_see_consultation(view_function):
    def decorator(*args, **kwargs):
        request = args[0]
        slug = kwargs.get("consultation_slug")
        obj = get_object_or_404(models.Consultation.objects.filter(slug=slug, users__in=[request.user]))

        return view_function(*args, **kwargs)

    return decorator

