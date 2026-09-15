from django.urls import path

from consultations.api.views_v2 import DataSetupV2RootView

urlpatterns = [
    path("", DataSetupV2RootView.as_view(), name="data-setup-v2-root"),
]
