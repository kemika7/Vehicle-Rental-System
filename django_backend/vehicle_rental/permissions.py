"""
Shared DRF permission classes used across all apps.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Grants access only to employees with role='admin'."""

    message = "Admin access required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )


class IsAdminOrReadOnly(BasePermission):
    """
    Safe methods (GET, HEAD, OPTIONS) → any authenticated user.
    Unsafe methods (POST, PUT, PATCH, DELETE) → admin only.
    """

    message = "Admin access required for write operations."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == "admin"


class IsAdminOrSelf(BasePermission):
    """Object-level: admin can access any object; employee can only access their own."""

    message = "You can only access your own profile."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        return obj == request.user
