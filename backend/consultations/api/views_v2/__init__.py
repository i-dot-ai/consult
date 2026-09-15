from typing import ClassVar

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from consultations.api.permissions import DataSetupV2Enabled


class DataSetupV2RootView(APIView):
    # DataSetupV2Enabled first so a disabled flag 404s before auth runs, hiding
    # the endpoint's existence rather than leaking it via a 401.
    permission_classes: ClassVar[list] = [DataSetupV2Enabled, IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok"})
