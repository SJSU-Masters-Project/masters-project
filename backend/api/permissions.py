"""Role-based permission classes.

``request.user`` is a ``Principal`` when authenticated and ``None`` when anonymous.
DRF's ``IsAuthenticated`` runs first (returns 401 for anonymous); these then enforce role.

A signed-in user may have no role yet (``role is None``) until they choose one via
``POST /api/v1/me/role`` (spec 04). In that case these classes deny with 403 ``role_required``
instead of the generic ``forbidden``, so the portal can route the user to role selection.
The wrong (but set) role still yields 403 ``forbidden``.
"""

from rest_framework.permissions import BasePermission

from api.errors import ApiError


class _RolePermission(BasePermission):
    allowed_roles: set[str] = set()
    message = "You do not have permission to do this."

    def has_permission(self, request, view):
        user = request.user
        role = getattr(user, "role", None)
        if user is not None and role is None:
            # Authenticated but no role chosen yet: distinct from a wrong role.
            raise ApiError(403, "role_required", "Choose a role before using this endpoint.")
        return user is not None and role in self.allowed_roles


class IsCandidate(_RolePermission):
    allowed_roles = {"candidate"}


class IsEmployer(_RolePermission):
    allowed_roles = {"employer"}


class IsAdmin(_RolePermission):
    allowed_roles = {"admin"}


class IsEmployerOrAdmin(_RolePermission):
    allowed_roles = {"employer", "admin"}
