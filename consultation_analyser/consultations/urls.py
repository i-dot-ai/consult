from django.urls import path

from .api.views import (
    DemographicAggregationsAPIView,
    DemographicOptionsAPIView,
    FilteredResponsesAPIView,
    QuestionInformationAPIView,
    ThemeAggregationsAPIView,
    ThemeInformationAPIView,
)
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
    # New modular endpoints
    # API endpoints
    path(
        "api/consultations/<uuid:consultation_id>/questions/<uuid:question_id>/demographic-options/",
        DemographicOptionsAPIView.as_view(),
        name="api_demographic_options",
    ),
    path(
        "api/consultations/<uuid:consultation_id>/questions/<uuid:question_id>/demographic-aggregations/",
        DemographicAggregationsAPIView.as_view(),
        name="api_demographic_aggregations",
    ),
    path(
        "api/consultations/<uuid:consultation_id>/questions/<uuid:question_id>/theme-information/",
        ThemeInformationAPIView.as_view(),
        name="api_theme_information",
    ),
    path(
        "api/consultations/<uuid:consultation_id>/questions/<uuid:question_id>/theme-aggregations/",
        ThemeAggregationsAPIView.as_view(),
        name="api_theme_aggregations",
    ),
    path(
        "api/consultations/<uuid:consultation_id>/questions/<uuid:question_id>/filtered-responses/",
        FilteredResponsesAPIView.as_view(),
        name="api_filtered_responses",
    ),
    path(
        "api/consultations/<uuid:consultation_id>/questions/<uuid:question_id>/question-information/",
        QuestionInformationAPIView.as_view(),
        name="api_question_information",
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
