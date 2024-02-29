from django.shortcuts import render
from django.http import HttpRequest


def show_question(request: HttpRequest):
    return render(request, "show_question.html")
