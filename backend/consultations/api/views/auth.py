import jwt
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.http import JsonResponse
from i_dot_ai_utilities.auth.auth_api import AuthApiClient
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import AccessToken

from consultations.api.serializers import TokenSerializer
from hosting_environment import HostingEnvironment

User = get_user_model()
logger = settings.LOGGER
client = AuthApiClient(
    app_name="consult", auth_api_url=settings.AUTH_API_URL, logger=logger, timeout=10
)


@api_view(["POST"])
@permission_classes([AllowAny])
def validate_token(request):
    logger.refresh_context()
    serializer = TokenSerializer(data=request.data)
    if not serializer.is_valid():
        return JsonResponse(serializer.errors, status=400)

    try:
        internal_access_token = serializer.validated_data["internal_access_token"]
        if HostingEnvironment.is_deployed():
            user_authorisation_info = client.get_user_authorisation_info(internal_access_token)
            if not user_authorisation_info.is_authorised:
                logger.error(
                    "{email} is not authenticated because {auth_reason}",
                    email=user_authorisation_info.email,
                    auth_reason=user_authorisation_info.auth_reason,
                )
                # TODO: reinstate this once DSIT (and other departments have been added to the consult clients)
                # return JsonResponse(data={"detail": "authentication failed"}, status=403)
            email = user_authorisation_info.email
        else:
            email = jwt.decode(internal_access_token, options={"verify_signature": False})["email"]

        user = User.objects.get(email=email)
    except User.DoesNotExist:
        logger.error("error authenticating request {error}", error="user does not exist")
        return JsonResponse(data={"detail": "authentication failed"}, status=403)
    except Exception as ex:
        logger.error("error authenticating request {error}", error=", ".join(map(str, ex.args)))
        return JsonResponse(data={"detail": "authentication failed"}, status=403)

    login(request, user)
    # Ensure session is created if it doesn't exist
    if not request.session.session_key:
        request.session.save()

    access_token = AccessToken.for_user(user)

    logger.info("user {email} authenticated", email=user.email)

    return JsonResponse(
        {
            "access": str(access_token),
            "sessionId": request.session.session_key,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    """
    Logout endpoint that flushes the Django session.
    Called by the frontend to clear backend session state.
    """
    logout(request)
    return JsonResponse({"status": "logged_out"})
