from django.conf import settings
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from magic_link.exceptions import InvalidLink
from magic_link.models import MagicLink
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from consultation_analyser.consultations.views.sessions import send_magic_link_if_email_exists

logger = settings.LOGGER


@api_view(["POST"])
def generate_magic_link(request):
    """
    create and email magic link
    """
    email = request.data.get("email")
    if not email:
        return Response({"detail": "Email required"}, status=400)

    send_magic_link_if_email_exists(request, email)

    return Response({"message": "Magic link sent"})


@api_view(["POST"])
def verify_magic_link(request) -> HttpResponse:
    """
    get access/refresh tokens.

    If the link is invalid, or the user is already logged in, then this
    view will raise a PermissionDenied, which will render the 403 template.

    """
    logger.refresh_context()
    token = request.data.get("token")
    if not token:
        return Response({"detail": "token required"}, status=400)
    link = get_object_or_404(MagicLink, token=token)
    try:
        link.validate()
        link.authorize(request.user)
        token = AccessToken.for_user(link.user)
    except (PermissionDenied, InvalidLink) as ex:
        link.audit(request, error=ex)
        logger.info("user {email} denied access", email=link.user.email)
        return JsonResponse(data={"detail": str(ex.args[0])}, status=403)
    else:
        logger.info("user {email} authenticated", email=link.user.email)
        link.audit(request)
        # Log the user into Django session
        login(request, link.user)
        # Ensure session is created if it doesn't exist
        if not request.session.session_key:
            request.session.save()
        return JsonResponse(
            {
                "access": str(token),
                "sessionId": request.session.session_key,
            }
        )
