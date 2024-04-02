from django.urls import path

from .views import consultations, pages, questions

urlpatterns = [
    path("", pages.home),
    path("consultations", consultations.show_questions),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>",
        questions.show,
        name="show_question",
    ),
]
