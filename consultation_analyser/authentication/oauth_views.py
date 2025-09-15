from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()
logger = settings.LOGGER


# @receiver(pre_social_login)
# def pre_social_login_receiver(sender, request, sociallogin, **kwargs):
#     """
#     Handle pre-social login logic.
#
#     This receiver:
#     1. Links social accounts to existing users by email
#     2. Ensures users have dashboard access if they don't exist
#     """
#     if sociallogin.account.provider == "openid_connect":
#         email = sociallogin.account.extra_data.get("email")
#         if email:
#             try:
#                 # Try to find existing user by email
#                 existing_user = User.objects.get(email=email)
#                 # Link the social account to the existing user
#                 sociallogin.connect(request, existing_user)
#             except User.DoesNotExist:
#                 # User will be created by allauth, but we need to set dashboard access
#                 pass
#


def oauth_success_view(request):
    """
    Handle successful OAuth login and set secure HTTP-only cookies.

    Flow: OAuth provider redirects here → Django creates/updates user →
    Django generates JWT → Set secure cookies → Redirect to Astro frontend
    """
    if not request.user.is_authenticated:
        return redirect(f"{settings.FRONTEND_URL}/sign-in?error=auth_failed")

    try:
        access_token = AccessToken.for_user(request.user)
    except Exception as e:
        # Log error and redirect to frontend with error
        logger.error(f"OAuth success view error: {e}")
        return redirect(f"{settings.FRONTEND_URL}/sign-in?error=server_error")

    # Create response redirecting to frontend dashboard

    response = redirect(settings.FRONTEND_URL)

    # Set secure cookies

    max_age = timedelta(hours=18).total_seconds()  # Match SIMPLE_JWT setting
    is_secure = request.is_secure() or not settings.DEBUG  # Force secure in production
    cookie_options = {
        "max_age": int(max_age),
        "httponly": True,  # Secure HTTP-only cookies
        "secure": is_secure,
        "samesite": "Lax" if settings.DEBUG else "Strict",  # Strict in production
        "domain": None,  # Will work for localhost:3000 and localhost:8000
    }

    response.set_cookie("access", str(access_token), **cookie_options)

    return response


def oauth_error_view(request):
    """Handle OAuth authentication errors."""
    error_type = request.GET.get("error", "oauth_error")
    return redirect(f"{settings.FRONTEND_URL}/sign-in?error={error_type}")
