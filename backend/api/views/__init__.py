from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


@extend_schema(exclude=True)
class NotFoundView(APIView):
    """Catch-all for unknown ``/api/`` URLs: always returns the 404 JSON envelope.

    Raising ``NotFound`` routes through ``api.errors.exception_handler`` so the response
    shape matches every other error, regardless of ``DEBUG``.
    """

    authentication_classes: list = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        raise NotFound("Resource not found.")

    post = put = patch = delete = get


not_found = NotFoundView.as_view()
