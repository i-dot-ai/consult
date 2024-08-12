from django.http import HttpResponseNotFound


class SupportAppStaffRequiredMiddleware:
    """Require staff users only for support app."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/support/"):
            if not request.user.is_authenticated:
                return HttpResponseNotFound()
            elif not request.user.is_staff:
                return HttpResponseNotFound()
        return response
