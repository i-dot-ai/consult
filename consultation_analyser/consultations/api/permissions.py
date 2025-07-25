from rest_framework import permissions

from .. import models


class HasDashboardAccess(permissions.BasePermission):
    """
    Allows access only to users who have dashboard access.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.has_dashboard_access


class CanSeeConsultation(permissions.BasePermission):
    """
    Allows access only to users who have access to the specific consultation.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        consultation_pk = view.kwargs.get("consultation_pk")
        if not consultation_pk:
            return False

        # Check if user has access to this consultation
        # Using exists() is more efficient than get_object_or_404 for permission checks
        return models.Consultation.objects.filter(
            id=consultation_pk, users__in=[request.user]
        ).exists()
