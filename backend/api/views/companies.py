from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.errors import ApiError
from api.permissions import IsEmployer
from api.repositories import companies as companies_repo
from api.serializers.companies import CompanyIn, CompanyOut, CompanyPatchIn
from api.timeutils import to_iso


def _company_out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "website": doc.get("website"),
        "description": doc.get("description"),
        "location": doc.get("location"),
        "created_at": to_iso(doc["created_at"]),
    }


class CompaniesView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsEmployer()]
        return [IsAuthenticated()]

    @extend_schema(request=CompanyIn, responses={201: CompanyOut})
    def post(self, request):
        serializer = CompanyIn(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc = companies_repo.create(request.user.user_id, serializer.validated_data)
        if doc is None:
            raise ApiError(409, "already_member", "You already belong to a company.")
        return Response(_company_out(doc), status=201)


class CompanyMineView(APIView):
    permission_classes = [IsAuthenticated, IsEmployer]

    @extend_schema(responses=CompanyOut)
    def get(self, request):
        doc = companies_repo.get_for_member(request.user.user_id)
        if doc is None:
            raise ApiError(404, "no_company", "You do not have a company yet.")
        return Response(_company_out(doc))


class CompanyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CompanyOut)
    def get(self, request, company_id):
        doc = companies_repo.get(company_id)
        if doc is None:
            raise ApiError(404, "not_found", "Resource not found.")
        return Response(_company_out(doc))

    @extend_schema(request=CompanyPatchIn, responses=CompanyOut)
    def patch(self, request, company_id):
        doc = companies_repo.get(company_id)
        if doc is None:
            raise ApiError(404, "not_found", "Resource not found.")
        if not companies_repo.is_member(doc, request.user.user_id):
            raise ApiError(403, "forbidden", "You are not a member of this company.")
        serializer = CompanyPatchIn(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = companies_repo.update(company_id, serializer.validated_data)
        return Response(_company_out(updated))


companies = CompaniesView.as_view()
company_mine = CompanyMineView.as_view()
company_detail = CompanyDetailView.as_view()
