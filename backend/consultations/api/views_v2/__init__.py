from typing import ClassVar

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from consultations.api.permissions import DataSetupV2Enabled


class DataSetupV2RootView(APIView):
    permission_classes: ClassVar[list] = [DataSetupV2Enabled, IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok"})
