import json
import logging

from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from consultation_analyser.consultations import models

from .decorators import user_can_see_consultation, user_can_see_dashboards

logger = logging.getLogger("upload")


def index(request: HttpRequest) -> HttpResponse:
    user = request.user
    consultations_for_user = models.Consultation.objects.filter(users=user)
    context = {
        "consultations": consultations_for_user,
        "user_has_dashboard_access": user.has_dashboard_access,
    }
    return render(request, "consultations/consultations/index.html", context)


def get_counts_of_sentiment(question: models.Question) -> dict:
    """Gives agree/disagree/unclear/no position counts for responses to the question."""
    total_responses = models.Response.objects.filter(question=question).count()

    annotations_with_sentiment = models.ResponseAnnotation.objects.filter(
        response__question=question, sentiment__isnull=False
    )

    number_in_agreement = annotations_with_sentiment.filter(
        sentiment=models.ResponseAnnotation.Sentiment.AGREEMENT
    ).count()
    number_in_disagreement = annotations_with_sentiment.filter(
        sentiment=models.ResponseAnnotation.Sentiment.DISAGREEMENT
    ).count()
    number_unclear = annotations_with_sentiment.filter(
        sentiment=models.ResponseAnnotation.Sentiment.UNCLEAR
    ).count()

    # Any responses not assigned a position
    number_no_position = (
        total_responses - number_in_agreement - number_in_disagreement - number_unclear
    )

    sentiment_counts = {
        "agreement": number_in_agreement,
        "disagreement": number_in_disagreement,
        "unclear": number_unclear,
        "no_position": number_no_position,
    }
    return sentiment_counts


def get_top_themes_for_question(
    question: models.Question, number_top_themes: int = 8
) -> list[dict]:
    # Get theme counts for questions with free text
    if not question.has_free_text:
        return []

    top_themes = (
        models.Theme.objects.filter(question=question, responseannotation__isnull=False)
        .annotate(theme_count=Count("responseannotation"))
        .order_by("-theme_count")
    )[:number_top_themes]

    top_themes_by_counts_list = []
    for theme in top_themes:
        output = {
            "theme": theme,
            "count": theme.theme_count,
        }
        top_themes_by_counts_list.append(output)
    return top_themes_by_counts_list


@user_can_see_dashboards
@user_can_see_consultation
def show(request: HttpRequest, consultation_slug: str) -> HttpResponse:
    # Dashboard page
    consultation = get_object_or_404(models.Consultation, slug=consultation_slug)
    questions = models.Question.objects.filter(consultation=consultation).order_by("number")

    all_questions = []
    for question in questions:
        question_dict = {"question": question}

        # Handle free text questions
        if question.has_free_text:
            question_dict["free_text_question_part"] = question  # For template compatibility
            top_themes_by_counts_list = get_top_themes_for_question(question)
            question_dict["theme_counts"] = top_themes_by_counts_list
            question_dict["sentiment_counts"] = get_counts_of_sentiment(question)

        # Handle multiple choice questions
        if question.has_multiple_choice:
            question_dict["multiple_option_question_part"] = question

            # Get option counts
            responses = models.Response.objects.filter(question=question).values("chosen_options")
            option_counts: dict[str, int] = {}
            for response in responses:
                for option in response["chosen_options"]:
                    option_counts[option] = option_counts.get(option, 0) + 1

            question_dict["multiple_option_counts"] = json.dumps(option_counts)

        all_questions.append(question_dict)

    # What is the right number per page?
    pagination = Paginator(all_questions, 2)
    page_index = request.GET.get("page", "1")
    current_page = pagination.page(page_index)
    paginated_questions = current_page.object_list

    context = {
        "consultation": consultation,
        "pagination": current_page,
        "questions_list": paginated_questions,
        "all_questions_list": all_questions,
    }
    return render(request, "consultations/consultations/show.html", context)
