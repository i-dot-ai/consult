from django.urls import path

from .views import consultations, pages, questions, responses, root, sessions

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
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/questions/<str:question_slug>/",
        questions.show,
        name="show_question",
    ),
    path(
        "consultations/<str:consultation_slug>/runs/<str:processing_run_slug>/sections/<str:section_slug>/questions/<str:question_slug>/",
        questions.show,
        name="show_question_runs",
    ),
    path(
        "consultations/<str:consultation_slug>/sections/<str:section_slug>/responses/<str:question_slug>/",
        responses.index,
        name="question_responses",
    ),
    path(
        "consultations/<str:consultation_slug>/runs/<str:processing_run_slug>/sections/<str:section_slug>/responses/<str:question_slug>/",
        responses.index,
        name="question_responses_runs",
    ),
    # authentication
    path("sign-in/", sessions.new, name="sign_in"),
    path("sign-out/", sessions.destroy, name="sign_out"),
    path("magic-link/<uuid:token>/", sessions.MagicLinkView.as_view(), name="magic_link"),
]
