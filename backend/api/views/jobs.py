from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.errors import ApiError
from api.events import emit_event
from api.pagination import page_response, parse_page_params
from api.permissions import IsEmployer
from api.repositories import companies as companies_repo
from api.repositories import jobs as jobs_repo
from api.repositories.jobs import to_job_api
from api.serializers.jobs import JobCreateIn, JobListOut, JobOut, JobPatchIn


def _is_member_or_admin(user, job: dict) -> bool:
    if user.role == "admin":
        return True
    company = companies_repo.get(job["company_id"])
    return companies_repo.is_member(company, user.user_id)


class JobsView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsEmployer()]
        return [AllowAny()]

    @extend_schema(
        parameters=[
            OpenApiParameter("q", str),
            OpenApiParameter("work_mode", str),
            OpenApiParameter("employment_type", str),
            OpenApiParameter("skill", str),
            OpenApiParameter("location", str),
            OpenApiParameter("company_id", str),
            OpenApiParameter("limit", int),
            OpenApiParameter("offset", int),
        ],
        responses=JobListOut,
        operation_id="jobs_list",
    )
    def get(self, request):
        page = parse_page_params(request.query_params)
        filters = {
            k: request.query_params.get(k)
            for k in ("q", "work_mode", "employment_type", "skill", "location", "company_id")
        }
        docs, total = jobs_repo.search(filters, page)
        items = [to_job_api(d) for d in docs]
        return Response(page_response(items, total, page))

    @extend_schema(request=JobCreateIn, responses={201: JobOut}, operation_id="jobs_create")
    def post(self, request):
        company = companies_repo.get_for_member(request.user.user_id)
        if company is None:
            raise ApiError(409, "no_company", "Create a company before posting jobs.")
        serializer = JobCreateIn(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc = jobs_repo.create(company, request.user.user_id, serializer.validated_data)
        return Response(to_job_api(doc), status=201)


class JobDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(responses=JobOut, operation_id="jobs_retrieve")
    def get(self, request, job_id):
        doc = jobs_repo.get(job_id)
        if doc is None:
            raise ApiError(404, "not_found", "Resource not found.")
        if doc["status"] != "open":
            user = request.user
            if user is None or not _is_member_or_admin(user, doc):
                raise ApiError(404, "not_found", "Resource not found.")
        return Response(to_job_api(doc))

    @extend_schema(request=JobPatchIn, responses=JobOut, operation_id="jobs_update")
    def patch(self, request, job_id):
        doc = jobs_repo.get(job_id)
        if doc is None:
            raise ApiError(404, "not_found", "Resource not found.")

        member = _is_member_or_admin(request.user, doc)
        if not member:
            # Hide drafts and closed jobs (404); an open job returns 403.
            if doc["status"] == "open":
                raise ApiError(403, "forbidden", "You cannot edit this job.")
            raise ApiError(404, "not_found", "Resource not found.")

        if doc["status"] == "closed":
            raise ApiError(409, "invalid_state", "Job is closed.", {"status": "closed"})

        serializer = JobPatchIn(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = jobs_repo.update(job_id, serializer.validated_data)
        if updated is None:
            raise ApiError(409, "invalid_state", "Job is closed.", {"status": "closed"})
        if updated["status"] == "open":
            emit_event(
                "job.updated", "job", updated["_id"], {"company_id": str(updated["company_id"])}
            )
        return Response(to_job_api(updated))


class JobPublishView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=JobOut, operation_id="jobs_publish")
    def post(self, request, job_id):
        doc = jobs_repo.get(job_id)
        if doc is None or not _is_member_or_admin(request.user, doc):
            raise ApiError(404, "not_found", "Resource not found.")
        updated = jobs_repo.publish(job_id)
        if updated is None:
            raise ApiError(
                409,
                "invalid_state",
                "Only a draft job can be published.",
                {"status": doc["status"]},
            )
        emit_event(
            "job.published", "job", updated["_id"], {"company_id": str(updated["company_id"])}
        )
        return Response(to_job_api(updated))


class JobCloseView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=JobOut, operation_id="jobs_close")
    def post(self, request, job_id):
        doc = jobs_repo.get(job_id)
        if doc is None or not _is_member_or_admin(request.user, doc):
            raise ApiError(404, "not_found", "Resource not found.")
        updated = jobs_repo.close(job_id)
        if updated is None:
            raise ApiError(
                409,
                "invalid_state",
                "Only an open job can be closed.",
                {"status": doc["status"]},
            )
        emit_event("job.closed", "job", updated["_id"], {"company_id": str(updated["company_id"])})
        return Response(to_job_api(updated))


class CompanyJobsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("status", str),
            OpenApiParameter("limit", int),
            OpenApiParameter("offset", int),
        ],
        responses=JobListOut,
        operation_id="company_jobs_list",
    )
    def get(self, request, company_id):
        company = companies_repo.get(company_id)
        if company is None:
            raise ApiError(404, "not_found", "Resource not found.")
        user = request.user
        privileged = user.role == "admin" or companies_repo.is_member(company, user.user_id)

        page = parse_page_params(request.query_params)
        status_filter = request.query_params.get("status")
        if privileged:
            statuses = [status_filter] if status_filter else None
        else:
            statuses = ["open"]
        docs, total = jobs_repo.list_for_company(company_id, statuses, page)
        items = [to_job_api(d) for d in docs]
        return Response(page_response(items, total, page))


jobs = JobsView.as_view()
job_detail = JobDetailView.as_view()
job_publish = JobPublishView.as_view()
job_close = JobCloseView.as_view()
company_jobs = CompanyJobsView.as_view()
