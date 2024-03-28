from django.urls import path

from .views import questions, pages

urlpatterns = [
<<<<<<< HEAD
    path("", pages.home),
=======
    path("", views.home),
    path("consultations", views.consultation),
>>>>>>> 2a93322 (Move question list to "/consultations")
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>",
        questions.show,
        name="show_question",
    ),
]
