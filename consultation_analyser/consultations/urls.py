from django.urls import path

from . import views

urlpatterns = [
    path("", views.home),
    path("questions/<str:slug>", views.show_question),
    path("consultation/<str:consultation_slug>/question-summary/<str:question_slug>", views.question_summary),
]
