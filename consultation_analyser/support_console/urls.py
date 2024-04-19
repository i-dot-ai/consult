from django.urls import path

from . import views

urlpatterns = [
    path("", views.support_home),
    path("sign-out/", views.sign_out),
    path("consultations/", views.show_consultations),
    path("consultations/<str:consultation_slug>/", views.show_consultation, name="support_consultation"),
]
