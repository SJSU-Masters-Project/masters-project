"""Test-only views and URLconf for exercising error handling and permissions."""

from api.permissions import IsAdmin, IsCandidate, IsEmployer, IsEmployerOrAdmin
from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class BoomView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def get(self, request):
        raise RuntimeError("boom")


class _OkView(APIView):
    def get(self, request):
        return Response({"ok": True})


class CandidateOnly(_OkView):
    permission_classes = [IsCandidate]


class EmployerOnly(_OkView):
    permission_classes = [IsEmployer]


class AdminOnly(_OkView):
    permission_classes = [IsAdmin]


class EmployerOrAdminOnly(_OkView):
    permission_classes = [IsEmployerOrAdmin]


urlpatterns = [
    path("api/_test/boom", BoomView.as_view()),
    path("api/_test/candidate", CandidateOnly.as_view()),
    path("api/_test/employer", EmployerOnly.as_view()),
    path("api/_test/admin", AdminOnly.as_view()),
    path("api/_test/employer-or-admin", EmployerOrAdminOnly.as_view()),
    path("api/", include("api.urls")),
]
