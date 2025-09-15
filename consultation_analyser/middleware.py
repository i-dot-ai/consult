from django.contrib.auth.middleware import LoginRequiredMiddleware
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


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
        response = self.get_response(request)
        if request.path.startswith("/support/"):
            # Must already be logged in from login required middleware.
            # Sign-out is excepted as we don't want to 404 on sign-out.
            if (not request.user.is_staff) and (not request.path.startswith("/support/sign-out/")):
                raise PermissionDenied("Access to support console requires staff privileges")
        return response


class LoginRequiredMiddleware404(LoginRequiredMiddleware):
    """Require login, 404 if no access."""

    def handle_no_permission(self, request, view_func):
        raise Http404


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

        return self.get_response(request)
