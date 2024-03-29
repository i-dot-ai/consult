from django.urls import path

<<<<<<< HEAD
from .views import consultations, pages, questions

urlpatterns = [
    path("", pages.home),
    path("consultations", consultations.show_questions),
=======
from .views import questions, pages, schema

urlpatterns = [
    path("", pages.home),
    path("schema", schema.show),
>>>>>>> 6a12671 (Add a schema page)
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>",
        questions.show,
        name="show_question",
    ),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/responses/<str:question_slug>",
        questions.show_responses,
    ),
    path("batch-example", pages.batch_example, name="batch_example"),
]
