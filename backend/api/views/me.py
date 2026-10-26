from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from api.ids import parse_object_id
from api.repositories import users as users_repo
from api.serializers.common import MeOut
from api.timeutils import to_iso


class MeView(APIView):
    @extend_schema(responses=MeOut)
    def get(self, request):
        user = users_repo.get_by_id(parse_object_id(request.user.user_id))
        return Response(
            {
                "id": str(user["_id"]),
                "email": user["email"],
                "role": user["role"],
                "created_at": to_iso(user["created_at"]),
            }
        )


me = MeView.as_view()
