import time

import sentry_sdk
import structlog
from django.conf import settings
from django.http import Http404
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

# Inbound/outbound header used to correlate a request across services.
CONTEXT_ID_HEADER = "x-context-id"
# Django exposes request headers via request.META with this transformation.
CONTEXT_ID_META_KEY = "HTTP_X_CONTEXT_ID"
# Cap on a trusted inbound context id; the header is untrusted, so bound the
# string we bind into log context and echo back to prevent log injection/replay.
MAX_CONTEXT_ID_LEN = 128
# Paths excluded from correlation logging (health checks are high-volume and noisy).
EXCLUDED_PATH_PREFIXES = ("/api/health",)


class RequestCorrelationMiddleware:
    """Give every request one ``context_id`` and log its metadata.

    Per request: refresh the logger context (so a reused gthread worker never
    carries a stale ``context_id``), reuse an inbound ``x-context-id`` header if
    present, bind request metadata, set the id as a Sentry tag, and echo it back
    on the response. Health paths are refreshed but excluded from correlation
    logging. Written against the current ``StructuredLogger`` so the OTel version
    is a drop-in later.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = settings.LOGGER

    def __call__(self, request):
        # Refresh even for excluded paths so a pooled thread never reuses a stale id.
        context_id = self._bind_context(request)

        if self._is_excluded(request.path):
            return self.get_response(request)

        sentry_sdk.set_tag("context_id", context_id)

        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # request.user resolves via AuthenticationMiddleware, so read it post-view.
        self.logger.set_context_field("user", self._user_identifier(request))
        self.logger.info(
            "{method} {path} {status}",
            method=request.method,
            path=request.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )

        response[CONTEXT_ID_HEADER] = context_id
        return response

    def _bind_context(self, request) -> str:
        """Reset context, honour an inbound context id, and bind request metadata."""
        self.logger.refresh_context()

        inbound_context_id = self._sanitise_context_id(request.META.get(CONTEXT_ID_META_KEY))
        if inbound_context_id:
            self.logger.set_context_field("context_id", inbound_context_id)

        self.logger.set_context_field("method", request.method)
        self.logger.set_context_field("path", request.path)

        # refresh_context() always binds a context_id, so it is guaranteed present.
        return str(structlog.contextvars.get_contextvars()["context_id"])

    @staticmethod
    def _sanitise_context_id(raw: str | None) -> str | None:
        """Bound and sanitise an untrusted inbound header before trusting it."""
        if not raw:
            return None
        candidate = raw[:MAX_CONTEXT_ID_LEN].strip()
        return candidate if candidate and candidate.isprintable() else None

    @staticmethod
    def _user_identifier(request) -> str:
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            return str(user.id)
        return "anonymous"

    @staticmethod
    def _is_excluded(path: str) -> bool:
        return path.startswith(EXCLUDED_PATH_PREFIXES)


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
