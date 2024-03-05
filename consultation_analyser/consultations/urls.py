from django.urls import path
from .views import home, show_question

urlpatterns = [path("", home), path("questions/<str:slug>", show_question)]
