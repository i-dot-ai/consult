from django.contrib.auth.middleware import LoginRequiredMiddleware
from django.http import Http404


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
                raise Http404
        return response


class LoginRequiredMiddleware404(LoginRequiredMiddleware):
    """Require login, 404 if no access."""

    def handle_no_permission(self, request, view_func):
        raise Http404
