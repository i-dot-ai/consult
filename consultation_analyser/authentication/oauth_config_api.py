from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET


@login_not_required
@csrf_exempt
@require_GET
def get_oauth_config(request):
    """Return OAuth configuration for frontend."""
    # Get the base URL from the request or settings
    base_url = request.build_absolute_uri("/")[:-1]  # Remove trailing slash

    config = {
        "authorization_url": f"{base_url}/accounts/oidc/gds/login/",
        "logout_url": f"{base_url}/sign-out/",
    }

    return JsonResponse(config)
