from django.urls import path

from . import oauth_config_api, oauth_views

urlpatterns = [
    path("oauth/success/", oauth_views.oauth_success_view, name="oauth_success"),
    path("oauth/error/", oauth_views.oauth_error_view, name="oauth_error"),
    path("oauth/callback/", oauth_views.oauth_success_view, name="oauth_callback"),
]

# API endpoints for frontend
api_urlpatterns = [
    path("api/oauth/config/", oauth_config_api.get_oauth_config, name="oauth_config"),
]

urlpatterns += api_urlpatterns
