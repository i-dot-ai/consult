from datetime import timedelta

from allauth.socialaccount.signals import pre_social_login
from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()
logger = settings.LOGGER


@receiver(pre_social_login)
def pre_social_login_receiver(sender, request, sociallogin, **kwargs):
    """
    Handle pre-social login logic.
    Links social accounts to existing users by email
    """
    if sociallogin.account.provider == "openid_connect":
        email = sociallogin.account.extra_data.get("email")
        if not email:
            raise ValueError("Email is required for OAuth authentication")
        user, _ = User.objects.get_or_create(email=email)
        sociallogin.connect(request, user)
        logger.info(f"OAuth login for email: {email}")


@csrf_exempt
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


@csrf_exempt
def oauth_error_view(request):
    """Handle OAuth authentication errors."""
    error_type = request.GET.get("error", "oauth_error")
    return redirect(f"{settings.FRONTEND_URL}/sign-in?error={error_type}")


def oauth_logout_view(request):
    """
    Handle user logout by clearing cookies and Django session.

    Flow: Frontend calls this endpoint → Clear cookies → Django logout →
    Return JSON response or redirect to frontend sign-in
    """
    # Create response - JSON for API calls, redirect for browser
    if (
        request.headers.get("Content-Type") == "application/json"
        or request.GET.get("format") == "json"
    ):
        response = JsonResponse({"message": "Logged out successfully"})
    else:
        response = redirect(f"{settings.FRONTEND_URL}/sign-in?logout=success")

    # Clear the JWT access token cookie
    response.delete_cookie(
        "access",
        domain=None,  # Match the domain used when setting
        samesite="Lax" if settings.DEBUG else "Strict",
    )

    # Clear Django session
    logout(request)

    logger.info(
        f"User logged out: {request.user.email if request.user.is_authenticated else 'anonymous'}"
    )

    return response
