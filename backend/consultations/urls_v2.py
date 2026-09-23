from django.urls import include, path
from rest_framework import routers

from consultations.api_v2.views.consultation import ConsultationViewSet

router = routers.DefaultRouter()
router.register("consultations", ConsultationViewSet, basename="consultation-v2")

urlpatterns = [
    path("api/v2/", include(router.urls)),
]
