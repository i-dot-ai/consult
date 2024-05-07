<<<<<<< HEAD
from django.shortcuts import get_object_or_404, redirect
=======
from django.shortcuts import redirect, get_object_or_404
from django.http.response import Http404
>>>>>>> d4a7ef9 (WIP)

from .. import models


def user_can_see_consultation(view_function):
    def decorator(*args, **kwargs):
        request = args[0]
        slug = kwargs.get("consultation_slug")

        # will kick out users by throwing a 404 if they don't own the consultation
        try:
            consultation = get_object_or_404(models.Consultation.objects.filter(slug=slug, users__in=[request.user]))
        except Http404 as e:
            if request.user.is_staff:
                consultation = get_object_or_404(models.Consultation.objects.filter(slug=slug))
            else:
                raise(e)

        if not consultation.has_themes():
            return redirect("/consultations/processing/")

        return view_function(*args, **kwargs)

    return decorator
