"""
URL configuration for consultation_analyser project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.urls import include, path
from rest_framework import routers
from rest_framework_nested.routers import NestedDefaultRouter

from consultation_analyser.api.views import ConsultationViewSet, QuestionViewSet, ResponseViewSet
from consultation_analyser.consultations import urls
from consultation_analyser.error_pages import views as error_views
from consultation_analyser.support_console import urls as support_console_urls

handler404 = error_views.error_404
handler500 = error_views.error_500

router = routers.DefaultRouter()
router.register(r"consultations", ConsultationViewSet, basename="consultations")
consultations_router = NestedDefaultRouter(router, r"consultations", lookup="consultation")
consultations_router.register(r"questions", QuestionViewSet, basename="consultation-questions")

questions_router = NestedDefaultRouter(consultations_router, r"questions", lookup="question")
questions_router.register(r"responses", ResponseViewSet, basename="consultation-question-responses")

urlpatterns = [
    path("", include(urls)),
    path("support/", include(support_console_urls)),
    path("api/", include(router.urls)),
    path("api/", include(consultations_router.urls)),
    path("api/", include(questions_router.urls)),
]

if settings.DEBUG:
    urlpatterns += debug_toolbar_urls()
