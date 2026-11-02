from django.urls import path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from api import views
from api.views import companies as company_views
from api.views import health as health_views
from api.views import jobs as job_views
from api.views import me as me_views
from api.views import profiles as profile_views
from api.views import resumes as resume_views

urlpatterns = [
    # Health at both the legacy and versioned paths.
    path("health/", health_views.health, name="health"),
    path("v1/health/", health_views.health, name="health-v1"),
    # Identity.
    path("v1/me", me_views.me, name="me"),
    path("v1/me/role", me_views.me_role, name="me-role"),
    # Companies (spec 02).
    path("v1/companies", company_views.companies, name="companies"),
    path("v1/companies/mine", company_views.company_mine, name="company-mine"),
    path("v1/companies/<str:company_id>", company_views.company_detail, name="company-detail"),
    path("v1/companies/<str:company_id>/jobs", job_views.company_jobs, name="company-jobs"),
    # Jobs (spec 02).
    path("v1/jobs", job_views.jobs, name="jobs"),
    path("v1/jobs/<str:job_id>", job_views.job_detail, name="job-detail"),
    path("v1/jobs/<str:job_id>/publish", job_views.job_publish, name="job-publish"),
    path("v1/jobs/<str:job_id>/close", job_views.job_close, name="job-close"),
    # Profiles (spec 03). Specific routes before the {userId} catch.
    path("v1/profiles/me/shared", profile_views.profile_shared, name="profile-shared"),
    path("v1/profiles/me", profile_views.profile_me, name="profile-me"),
    path("v1/profiles/<str:user_id>", profile_views.profile_public, name="profile-public"),
    # Resumes (spec 03). download before {id}.
    path("v1/resumes", resume_views.resumes, name="resumes"),
    path(
        "v1/resumes/<str:resume_id>/download", resume_views.resume_download, name="resume-download"
    ),
    path("v1/resumes/<str:resume_id>", resume_views.resume_detail, name="resume-detail"),
    # OpenAPI schema and docs.
    path("v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="docs",
    ),
    # Catch-all: any other /api/ URL returns the JSON 404 envelope. Keep this last.
    re_path(r"^.*$", views.not_found, name="not-found"),
]
