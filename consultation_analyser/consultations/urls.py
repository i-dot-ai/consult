from django.urls import path

from .api.views import DemographicAggregationsAPIView, DemographicOptionsAPIView
from .views import answers, consultations, pages, questions, root, sessions

urlpatterns = [
    # public urls
    path("", root.root, name="root"),
    path("how-it-works/", pages.how_it_works, name="how_it_works"),
    path("data-sharing/", pages.data_sharing, name="data_sharing"),
    path("get-involved/", pages.get_involved, name="get_involved"),
    path("privacy/", pages.privacy, name="privacy"),
    # login required
    path("consultations/", consultations.index, name="consultations"),
    path("consultations/<str:consultation_slug>/", consultations.show, name="consultation"),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/",
        answers.index,
        name="question_responses",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/json/",
        answers.question_responses_json,
        name="question_responses_json",
    ),
    # New modular endpoints
    # API endpoints
    path(
        "api/consultations/<str:consultation_slug>/questions/<str:question_slug>/demographic-options/",
        DemographicOptionsAPIView.as_view(),
        name="api_demographic_options",
    ),
    path(
        "api/consultations/<str:consultation_slug>/questions/<str:question_slug>/demographic-aggregations/",
        DemographicAggregationsAPIView.as_view(),
        name="api_demographic_aggregations",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/theme_information/",
        answers.theme_information,
        name="theme_information",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/theme_aggregations/",
        answers.theme_aggregations,
        name="theme_aggregations",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/filtered_responses/",
        answers.filtered_responses,
        name="filtered_responses",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/question_information/",
        answers.question_information,
        name="question_information",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/show-next/",
        answers.show_next,
        name="show_next_response",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/<uuid:response_id>/",
        answers.show,
        name="show_response",
    ),
    path(
        "consultations/<str:consultation_slug>/review-questions/",
        questions.index,
        name="review_free_text_questions",
    ),
    # authentication
    path("sign-in/", sessions.new, name="sign_in"),
    path("sign-out/", sessions.destroy, name="sign_out"),
    path("magic-link/<uuid:token>/", sessions.MagicLinkView.as_view(), name="magic_link"),
]
