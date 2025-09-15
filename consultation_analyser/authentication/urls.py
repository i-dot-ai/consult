from django.urls import path

from . import oauth_views

urlpatterns = [
    path("oauth/callback/", oauth_views.oauth_success_view, name="oauth_callback"),
    path("oauth/error/", oauth_views.oauth_error_view, name="oauth_error"),
    path("oauth/logout/", oauth_views.oauth_logout_view, name="oauth_logout"),
]
