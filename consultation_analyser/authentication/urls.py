from django.urls import path

from . import oauth_views

urlpatterns = [
    path("callback/", oauth_views.oauth_success_view, name="oauth_callback"),
    path("error/", oauth_views.oauth_error_view, name="oauth_error"),
    path("logout/", oauth_views.oauth_logout_view, name="oauth_logout"),
]
