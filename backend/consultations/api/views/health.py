from datetime import datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(_request) -> Response:
    return Response({"status": "ok", "timestamp": datetime.now().isoformat()})
