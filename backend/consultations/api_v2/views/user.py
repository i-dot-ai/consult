from typing import ClassVar

from rest_framework import status
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from authentication.models import User
from consultations.api_v2.serializers import UserCreateSerializerV2


class UserViewSet(CreateModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializerV2
    permission_classes: ClassVar[list] = [IsAuthenticated, IsAdminUser]

    def create(self, request, *args, **kwargs):
        emails = request.data.get("emails")
        if not isinstance(emails, list):
            return super().create(request, *args, **kwargs)

        created = []
        errors = []
        for email in emails:
            serializer = self.get_serializer(data={"email": email})
            if serializer.is_valid():
                created.append(serializer.save())
            else:
                errors.append({"email": email, "errors": serializer.errors})

        if errors:
            return Response(
                {"detail": "Some users not created.", "errors": errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            self.get_serializer(created, many=True).data, status=status.HTTP_201_CREATED
        )
