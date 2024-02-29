from django.urls import path
from .views import show_question

urlpatterns = [path("questions/how-should-funding-be-allocated", show_question)]
