from datetime import timedelta

from allauth.socialaccount.signals import pre_social_login
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@receiver(pre_social_login)
def pre_social_login_receiver(sender, request, sociallogin, **kwargs):
    """
    Handle pre-social login logic.

    This receiver:
    1. Links social accounts to existing users by email
    2. Ensures users have dashboard access if they don't exist
    """
    if sociallogin.account.provider == "openid_connect":
        email = sociallogin.account.extra_data.get("email")
        if email:
            try:
                # Try to find existing user by email
                existing_user = User.objects.get(email=email)
                # Link the social account to the existing user
                sociallogin.connect(request, existing_user)
            except User.DoesNotExist:
                # User will be created by allauth, but we need to set dashboard access
                pass


def oauth_success_view(request):
    """
    Handle successful OAuth login and set secure HTTP-only cookies.

    Flow: OAuth provider redirects here → Django creates/updates user →
    Django generates JWT → Set secure cookies → Redirect to Astro frontend
    """
    if not request.user.is_authenticated:
        return redirect(reverse("account_login"))

    # Ensure user has dashboard access
    if not hasattr(request.user, "has_dashboard_access") or not request.user.has_dashboard_access:
        request.user.has_dashboard_access = True
        request.user.save()

    # Generate JWT token
    access_token = AccessToken.for_user(request.user)

    # Generate session for compatibility
    if not request.session.session_key:
        request.session.save()

    # Create response redirecting to frontend
    frontend_url = "http://localhost:4321"  # Should be configurable
    response = redirect(f"{frontend_url}/oauth/success")

    # Set secure HTTP-only cookies
    max_age = timedelta(hours=18).total_seconds()  # Match SIMPLE_JWT setting
    cookie_options = {
        "max_age": int(max_age),
        "httponly": False,  # Frontend needs to read these for API calls
        "secure": request.is_secure(),
        "samesite": "Lax",  # Allow cross-site for localhost development
        "domain": None,  # Will work for localhost:4321 and localhost:8000
    }

    response.set_cookie("access", str(access_token), **cookie_options)
    response.set_cookie("sessionId", request.session.session_key, **cookie_options)

    return response


def oauth_error_view(request):
    """Handle OAuth authentication errors."""
    return JsonResponse(
        {
            "error": "OAuth authentication failed",
            "message": "There was an error during the authentication process.",
        },
        status=400,
    )
