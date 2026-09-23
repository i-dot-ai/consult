from django.db.models import Q
from rest_framework import permissions

from consultations import models


class CanSeeConsultationV2(permissions.BasePermission):
    """
    Allows access only to superusers or users who are assigned to or own
    the specific consultation.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if getattr(request.user, "is_staff", False):
            return True

        consultation_pk = view.kwargs.get("consultation_pk") or view.kwargs.get("pk")
        if not consultation_pk:
            # No consultation specified so no consultation to restrict access to
            return True

        # Grant access if the user is assigned to or owns the consultation
        return (
            models.Consultation.objects.filter(id=consultation_pk)
            .filter(Q(users=request.user) | Q(created_by=request.user))
            .exists()
        )


class IsConsultationOwnerOrSuperuser(permissions.BasePermission):
    """
    Allows access only to staff users or users who own the specific consultation
    (i.e. are recorded as created_by). Use this to protect views that assigned
    users should not be able to access, such as deletion or configuration.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if getattr(request.user, "is_staff", False):
            return True

        consultation_pk = view.kwargs.get("consultation_pk") or view.kwargs.get("pk")
        if not consultation_pk:
            return False

        return models.Consultation.objects.filter(
            id=consultation_pk, created_by=request.user
        ).exists()
