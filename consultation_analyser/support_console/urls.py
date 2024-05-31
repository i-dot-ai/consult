from django.urls import path
from django.shortcuts import redirect

from .views import consultations, pages, users

urlpatterns = [
    path("", lambda request: redirect('/support/consultations/')),
    path("sign-out/", pages.sign_out),
    path("users/", users.index),
    path("users/new/", users.new),
    path("users/<int:user_id>/", users.show),
    path("consultations/", consultations.index),
    path("consultations/<uuid:consultation_id>/", consultations.show, name="support_consultation"),
    path(
        "consultations/<uuid:consultation_id>/delete/",
        consultations.delete,
        name="delete_consultation",
    ),
]
