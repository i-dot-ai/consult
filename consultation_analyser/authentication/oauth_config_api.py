from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def get_oauth_config(request):
    """Return OAuth configuration for frontend."""
    # Get the base URL from the request or settings
    base_url = request.build_absolute_uri("/")[:-1]  # Remove trailing slash

    config = {
        "authorization_url": f"{base_url}/accounts/openid_connect/security_gov_uk/login/",
        "logout_url": f"{base_url}/sign-out/",
    }

    return JsonResponse(config)
