from django.urls import path

from . import views

urlpatterns = [
    path("", views.home),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>",
        views.show_question,
    ),
]
