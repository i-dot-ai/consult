from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from consultation_analyser.consultations import models
from consultation_analyser.consultations.api.filters import UserFilter
from consultation_analyser.consultations.api.serializers import UserSerializer, ConsultationSerializer


class UserViewSet(ModelViewSet):
    def create(self, request, *args, **kwargs):
        # Support both single and bulk creation
        data = request.data
        has_dashboard_access = data.get("has_dashboard_access", False)

        # If 'emails' is present and is a list, treat as bulk creation
        if isinstance(data.get("emails"), list):
            emails = data["emails"]
            created_users = []
            errors = []
            for email in emails:
                serializer = self.get_serializer(
                    data={"email": email, "has_dashboard_access": has_dashboard_access}
                )
                if serializer.is_valid():
                    user = serializer.save()
                    created_users.append(user)
                else:
                    errors.append({"email": email, "errors": serializer.errors})
            if errors:
                return Response({"detail": "Some users not created.", "errors": errors}, status=400)
            return Response(self.get_serializer(created_users, many=True).data, status=201)

        # Otherwise, treat as single user creation using default DRF behavior
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        queryset = models.User.objects.all()
        filterset = self.filterset_class(self.request.GET, queryset=queryset, request=self.request)
        return filterset.qs.distinct()

    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    pagination_class = PageNumberPagination
    filterset_class = UserFilter

    @action(detail=True, methods=["get"], url_path="consultations")
    def consultations(self, request, pk=None):
        """
        Get all consultations that a specific user belongs to.
        """
        user = self.get_object()
        consultations = models.Consultation.objects.filter(users=user)
        serializer = ConsultationSerializer(consultations, many=True, context={'request': request})
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Returns the current logged-in user's information
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
