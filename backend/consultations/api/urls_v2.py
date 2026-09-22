from rest_framework import routers

from .views_v2.consultation import ConsultationViewSet

router = routers.DefaultRouter()
router.register("consultations", ConsultationViewSet, basename="consultation-v2")

urlpatterns = router.urls
