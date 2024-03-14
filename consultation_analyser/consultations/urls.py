from django.urls import path

from . import views

urlpatterns = [
    path("", views.home),
    path(
        "consultation/<str:consultation_slug>/section/<str:section_slug>/question/<str:question_slug>/",
        views.show_question,
    ),
]
