import jwt
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from magic_link.exceptions import InvalidLink
from magic_link.models import MagicLink
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken

from consultation_analyser.consultations.views.sessions import send_magic_link_if_email_exists


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
        return JsonResponse(data={"detail": str(ex.args[0])}, status=403)
    else:
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


User = get_user_model()
logger = settings.LOGGER


class TokenSerializer(serializers.Serializer):
    internal_access_token = serializers.CharField()


@api_view(["POST"])
def validate_token(request):
    serializer = TokenSerializer(data=request.data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    try:
        internal_access_token = serializer.validated_data["internal_access_token"]
        email = jwt.decode(internal_access_token, options={"verify_signature": False})["email"]
        user, _ = User.objects.get_or_create(email=email)
    except (jwt.DecodeError, KeyError) as ex:
        logger.error("error authenticating request {error}", error=str(ex.args[0]))
        return JsonResponse(data={"detail": "authentication failed"}, status=403)

    login(request, user)
    # Ensure session is created if it doesn't exist
    if not request.session.session_key:
        request.session.save()

    access_token = AccessToken.for_user(user)

    return JsonResponse(
        {
            "access": str(access_token),
            "sessionId": request.session.session_key,
        }
    )
