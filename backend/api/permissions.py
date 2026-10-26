"""Role-based permission classes.

``request.user`` is a ``Principal`` when authenticated and ``None`` when anonymous.
DRF's ``IsAuthenticated`` runs first (returns 401 for anonymous); these then enforce role
and return 403 ``forbidden`` for the wrong role.
"""

from rest_framework.permissions import BasePermission


class _RolePermission(BasePermission):
    allowed_roles: set[str] = set()
    message = "You do not have permission to do this."

    def has_permission(self, request, view):
        user = request.user
        return user is not None and getattr(user, "role", None) in self.allowed_roles


class IsCandidate(_RolePermission):
    allowed_roles = {"candidate"}


class IsEmployer(_RolePermission):
    allowed_roles = {"employer"}


class IsAdmin(_RolePermission):
    allowed_roles = {"admin"}


class IsEmployerOrAdmin(_RolePermission):
    allowed_roles = {"employer", "admin"}
