import jwt
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from i_dot_ai_utilities.auth.auth_api import AuthApiClient
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import AccessToken

from consultation_analyser.hosting_environment import HostingEnvironment

User = get_user_model()
logger = settings.LOGGER
client = AuthApiClient(app_name="consult", auth_api_url=settings.AUTH_API_URL, logger=logger)


def get_email_from_token(token):
    if HostingEnvironment.is_deployed():
        return client.get_user_authorisation_info(token).email
    return jwt.decode(token, options={"verify_signature": False})["email"]


class TokenSerializer(serializers.Serializer):
    internal_access_token = serializers.CharField()


@api_view(["POST"])
def validate_token(request):
    serializer = TokenSerializer(data=request.data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    try:
        internal_access_token = serializer.validated_data["internal_access_token"]
        email = get_email_from_token(internal_access_token)
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
