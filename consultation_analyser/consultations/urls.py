from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter

from .api.views import (
    ConsultationViewSet,
    QuestionViewSet,
    RespondentViewSet,
    ResponseViewSet,
    ThemeViewSet,
    generate_magic_link,
    get_current_user,
    get_git_sha,
    verify_magic_link,
)
from .views import answers, pages, questions, root, sessions

router = routers.DefaultRouter()
router.register("consultations", ConsultationViewSet, basename="consultations")

consultations_router = NestedDefaultRouter(router, "consultations", lookup="consultation")

consultations_router.register("respondents", RespondentViewSet, basename="respondent")
consultations_router.register("questions", QuestionViewSet, basename="question")
consultations_router.register("themes", ThemeViewSet, basename="theme")
consultations_router.register("responses", ResponseViewSet, basename="response")

questions_router = NestedDefaultRouter(consultations_router, "questions", lookup="question")
themes_router = NestedDefaultRouter(consultations_router, "themes", lookup="theme")


urlpatterns = [
    # public urls
    path("", root.root, name="root"),
    path("how-it-works/", pages.how_it_works, name="how_it_works"),
    path("data-sharing/", pages.data_sharing, name="data_sharing"),
    path("get-involved/", pages.get_involved, name="get_involved"),
    path("privacy/", pages.privacy, name="privacy"),
    # New modular endpoints
    # API endpoints
    path("api/", include(router.urls)),
    path("api/", include(consultations_router.urls)),
    path("api/", include(questions_router.urls)),
    path("api/", include(themes_router.urls)),
    path("api/user/", get_current_user, name="user"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path(
        "evaluations/<uuid:consultation_id>/questions/<uuid:question_id>/show-next/",
        answers.show_next,
        name="show_next_response",
    ),
    path(
        "evaluations/<uuid:consultation_id>/questions/<uuid:question_id>/responses/<uuid:response_id>/",
        answers.show,
        name="show_response",
    ),
    path(
        "evaluations/<uuid:consultation_id>/questions/",
        questions.index,
        name="review_free_text_questions",
    ),
    # authentication
    path("sign-in/", sessions.new, name="sign_in"),
    path("sign-out/", sessions.destroy, name="sign_out"),
    path("magic-link/<uuid:token>/", sessions.MagicLinkView.as_view(), name="magic_link"),
    # JWT
    path("api/magic-link/", generate_magic_link, name="token-magic-link"),
    path("api/token/", verify_magic_link, name="create-token"),
    path("git-sha/", get_git_sha, name="git-sha"),
]
