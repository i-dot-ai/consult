import logging

from django.http import Http404
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware:
    """Authenticate JWT tokens for regular Django views (non-DRF)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        # Try to authenticate using JWT token from Authorization header
        try:
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            if auth_header and auth_header.startswith("Bearer "):
                result = self.jwt_auth.authenticate(request)
                if result is not None:
                    user, token = result
                    request.user = user
                    # Mark as authenticated via JWT for later middleware
                    request._cached_user = user
        except (InvalidToken, TokenError):
            # If JWT is invalid, let AuthenticationMiddleware handle it normally
            pass

        response = self.get_response(request)
        return response


class SupportAppStaffRequiredMiddleware:
    """Require staff users only for support app."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/support/"):
            if not request.user.is_authenticated:
                raise Http404

            # Must already be logged in from login required middleware.
            # Sign-out is excepted as we don't want to 404 on sign-out.
            if (not request.user.is_staff) and (not request.path.startswith("/support/sign-out/")):
                raise Http404
        response = self.get_response(request)
        return response


class CSRFExemptMiddleware:
    """
    Middleware to disable CSRF protection for support console routes during migration.

    This is a temporary measure while we're proxying /support/ routes through the
    Astro frontend. Once the migration is complete, this middleware should be removed.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Disable CSRF checks for support console routes
        if request.path.startswith("/support/"):
            setattr(request, "_dont_enforce_csrf_checks", True)

        # Debug logging for admin CSRF issues
        if request.path.startswith("/admin/") and request.method == "POST":
            csrf_cookie = request.COOKIES.get("csrftoken", "NOT_SET")
            csrf_post = request.POST.get("csrfmiddlewaretoken", "NOT_SET")
            csrf_header = request.META.get("HTTP_X_CSRFTOKEN", "NOT_SET")
            
            logger.info(
                f"[CSRF Debug] Admin POST to {request.path} - "
                f"Cookie: {csrf_cookie[:20]}..., "
                f"POST body: {csrf_post[:20]}..., "
                f"Header: {csrf_header[:20] if csrf_header != 'NOT_SET' else 'NOT_SET'}"
            )

        return self.get_response(request)
