from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def get_git_sha(_request) -> Response:
    return Response({"sha": settings.GIT_SHA})
