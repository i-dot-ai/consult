from django.urls import include, path
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter

from .api.views import (
    ConsultationViewSet,
    QuestionViewSet,
)
from .views import answers, consultations, pages, questions, root, sessions

router = routers.DefaultRouter()
router.register("consultations", ConsultationViewSet, basename="consultations")

consultations_router = NestedDefaultRouter(router, r"consultations", lookup="consultation")
consultations_router.register("questions", QuestionViewSet, basename="question")

questions_router = NestedDefaultRouter(consultations_router, r"questions", lookup="question")


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
    path("api/", include(router.urls)),
    path("api/", include(consultations_router.urls)),
    path("api/", include(questions_router.urls)),
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
