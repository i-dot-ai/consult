from django.urls import path

from .views import questions, pages

urlpatterns = [
    path("", pages.home),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>",
        questions.show,
        name="show_question",
    ),
]
