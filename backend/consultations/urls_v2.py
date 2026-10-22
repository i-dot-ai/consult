from django.urls import include, path
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter

from consultations.api_v2.views.consultation import ConsultationViewSet
from consultations.api_v2.views.question import QuestionViewSet
from consultations.api_v2.views.user import UserViewSet, get_current_user

router = routers.DefaultRouter()
router.register("consultations", ConsultationViewSet, basename="consultation-v2")
router.register("users", UserViewSet, basename="user-v2")

consultations_router = NestedDefaultRouter(router, "consultations", lookup="consultation")
consultations_router.register("questions", QuestionViewSet, basename="question-v2")

urlpatterns = [
    path("api/v2/", include(router.urls)),
    path("api/v2/", include(consultations_router.urls)),
    path("api/v2/user/", get_current_user, name="user"),
]
