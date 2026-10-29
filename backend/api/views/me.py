from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from api.errors import ApiError
from api.ids import parse_object_id
from api.repositories import users as users_repo
from api.serializers.common import MeOut, RoleIn
from api.timeutils import to_iso


def _me_out(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "created_at": to_iso(user["created_at"]),
    }


class MeView(APIView):
    @extend_schema(responses=MeOut)
    def get(self, request):
        user = users_repo.get_by_id(parse_object_id(request.user.user_id))
        return Response(_me_out(user))


class MeRoleView(APIView):
    """POST /api/v1/me/role — a signed-in user with no role picks one, once.

    Returns the updated user (200). If the role is already set, returns 409
    ``role_already_set`` (spec 04, Requirement 2.3). ``admin`` cannot be chosen here;
    the serializer only accepts ``candidate`` or ``employer`` (Requirement 2.5).
    """

    @extend_schema(request=RoleIn, responses={200: MeOut})
    def post(self, request):
        serializer = RoleIn(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data["role"]
        user = users_repo.set_role(request.user.user_id, role)
        if user is None:
            raise ApiError(409, "role_already_set", "Your role is already set.")
        return Response(_me_out(user))


me = MeView.as_view()
me_role = MeRoleView.as_view()
