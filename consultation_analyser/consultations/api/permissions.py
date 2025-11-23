from django.conf import settings
from rest_framework import permissions

from .. import models

logger = settings.LOGGER


class HasDashboardAccess(permissions.BasePermission):
    """
    Allows access only to users who have dashboard access.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            logger.info("user {email} not authenticated", email=request.user.email)
            return False
        if not request.user.has_dashboard_access:
            logger.info("user {email} doesnt have dashboard access", email=request.user.email)
            return False
        return True


class CanSeeConsultation(permissions.BasePermission):
    """
    Allows access only to users who have access to the specific consultation.
    """

    def has_permission(self, request, view):
        logger.info(
            "CanSeeConsultation permission check - user: {email}, view.kwargs: {kwargs}, path: {path}",
            email=getattr(request.user, "email", "unknown"),
            kwargs=view.kwargs,
            path=request.path,
        )

        if not request.user.is_authenticated:
            logger.info("user {email} not authenticated", email=request.user.email)
            return False

        # Allow staff/admin users early — they should be able to pass view-level
        # permission checks so that object-level checks (or IsAdminUser) can run.
        if getattr(request.user, "is_staff", False):
            logger.info("user {email} is staff", email=request.user.email)
            return True

        consultation_pk = view.kwargs.get("consultation_pk") or view.kwargs.get("pk")
        logger.info("consultation_pk extracted: {pk}", pk=consultation_pk)

        if not consultation_pk:
            # No consultation specified so no consultation to restrict access to
            logger.info("No consultation_pk found, allowing access")
            return True

        # Check if user has access to this consultation
        # Using exists() is more efficient than get_object_or_404 for permission checks
        if not models.Consultation.objects.filter(
            id=consultation_pk, users__in=[request.user]
        ).exists():
            logger.info(
                "user {email} doesnt have access to this consultation", email=request.user.email
            )
            return False

        logger.info("user {email} has access to this consultation", email=request.user.email)
        return True
