from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import render

from .. import models


def get_applied_filters(request: HttpRequest):
    return {
        "keyword": request.GET.get("keyword", ""),
        "theme": request.GET.get("theme", "All"),
        "opinion": request.GET.get("opinion", "All"),
    }


def get_filtered_responses(question: models.Question, applied_filters):
    queryset = models.Answer.objects.filter(question=question, free_text__icontains=applied_filters["keyword"])
    if applied_filters["theme"] != "All" and applied_filters["theme"] != "No theme":
        queryset = queryset.filter(theme=applied_filters["theme"])
    # TO DO: handle answers with "No theme"
    if applied_filters["opinion"] != "All":
        queryset = queryset.filter(multiple_choice_responses=applied_filters["opinion"])
    return queryset


def show(request: HttpRequest, consultation_slug: str, section_slug: str, question_slug: str):
    question = models.Question.objects.get(
        slug=question_slug, section__slug=section_slug, section__consultation__slug=consultation_slug
    )
    themes_for_question = models.Theme.objects.filter(answer__question=question)
    total_responses = models.Answer.objects.filter(question=question).count()
    applied_filters = get_applied_filters(request)
    responses = get_filtered_responses(question, applied_filters)

    # pagination
    pagination = Paginator(responses, 5)
    page_index = request.GET.get("page", "1")
    current_page = pagination.page(page_index)
    paginated_responses = current_page.object_list

    context = {
        "question": question,
        "responses": paginated_responses,
        "total_responses": total_responses,
        "applied_filters": applied_filters,
        "themes_for_question": themes_for_question,
        "pagination": current_page,
    }

    return render(request, "show_responses.html", context)
