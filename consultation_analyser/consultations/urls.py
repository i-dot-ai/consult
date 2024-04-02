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
<<<<<<< HEAD
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/responses/<str:question_slug>",
        questions.show_responses,
    ),
    path("batch-example", views.batch_example, name="batch_example"),
=======
    path("batch-example", pages.batch_example, name="batch_example"),
>>>>>>> 2540631 (Move views to refactored pages, some tweaks to batch job example view.)
]
