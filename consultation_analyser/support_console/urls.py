from django.urls import path

from .views import consultations, pages, users

urlpatterns = [
    path("", pages.support_home),
    path("sign-out/", pages.sign_out),
    path("users/", users.index),
    path("consultations/", consultations.index),
    path("consultations/<str:consultation_slug>/", consultations.show, name="support_consultation"),
]
