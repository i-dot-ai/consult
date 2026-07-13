from django.conf import settings
from django.http import Http404
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class RequestLoggingContextMiddleware:
    """Refresh the structured-logging context at the start of every request.

    settings.LOGGER's context_id is bound once, at settings-import time, in
    whichever thread performs the import. Gunicorn's gthread workers reuse a
    pool of threads across requests, so without this, a request handled on any
    other thread inherits "unknown" or a stale context_id left over from a
    previous request/task on that thread — breaking correlation between this
    request's logs and any batch jobs it submits.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        settings.LOGGER.refresh_context()
        return self.get_response(request)


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

        return self.get_response(request)
