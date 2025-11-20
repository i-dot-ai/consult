import jwt
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import JsonResponse
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import AccessToken

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
