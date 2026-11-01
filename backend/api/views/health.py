from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.mongo import get_database
from api.serializers.common import HealthOut


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(responses=HealthOut, auth=[])
    def get(self, request):
        version = getattr(settings, "APP_VERSION", "dev")
        try:
            get_database().command("ping")
            return Response({"status": "ok", "mongodb": "connected", "version": version})
        except Exception as exc:
            body = {"status": "degraded", "mongodb": "unavailable", "version": version}
            if settings.DEBUG:
                body["detail"] = str(exc)
            return Response(body, status=503)


health = HealthView.as_view()
