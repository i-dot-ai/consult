import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

User = get_user_model()


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


class EdgeJWTAuthenticationMiddleware:
    """Authenticate JWT tokens from edge authentication (no signature verification)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Try to authenticate using JWT token from Authorization header
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            try:
                # Decode JWT without signature verification (edge handles validation)
                payload = jwt.decode(token, options={"verify_signature": False})

                # Try email field first (for edge tokens)
                if "email" in payload:
                    email = payload["email"]
                    try:
                        user = User.objects.get(email=email)
                        request.user = user
                        request._cached_user = user
                    except User.DoesNotExist:
                        raise PermissionDenied("User not found in system")
                # Fallback to user_id field (for existing DRF tokens)
                elif "user_id" in payload:
                    user_id = payload["user_id"]
                    try:
                        user = User.objects.get(id=user_id)
                        request.user = user
                        request._cached_user = user
                    except User.DoesNotExist:
                        raise PermissionDenied("User not found in system")
                else:
                    raise PermissionDenied("No valid user identifier in JWT", auth_header)

            except jwt.DecodeError:
                raise PermissionDenied("Invalid JWT format")

        response = self.get_response(request)
        return response


class SupportAppStaffRequiredMiddleware:
    """Require staff users only for support app."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/support/"):
            if not request.user.is_authenticated:
                return redirect(settings.SIGNIN_URL)

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
