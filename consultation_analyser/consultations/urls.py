from django.urls import path

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
        "consultations/<str:consultation_slug>/questions/<str:question_slug>/",
        questions.show,
        name="show_question",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/",
        answers.index,
        name="question_responses",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/show-next/",
        answers.show_next,
        name="show_next_response",
    ),
    path(
        "consultations/<str:consultation_slug>/responses/<str:question_slug>/<str:response_id>/",
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
