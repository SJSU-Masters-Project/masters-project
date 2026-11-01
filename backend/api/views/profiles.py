import logging

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.contracts import FULL
from api.errors import ApiError
from api.events import emit_event
from api.ids import parse_object_id
from api.permissions import IsCandidate
from api.repositories import profiles as profiles_repo
from api.repositories import resumes as resumes_repo
from api.serializers.profiles import ProfileBodyValidator, ProfileOut, SharedProfileOut
from api.timeutils import to_iso

logger = logging.getLogger("api")

SECTION_KEYS = (
    "personal",
    "academic",
    "certifications",
    "achievements",
    "career",
    "jobPreferences",
)


def _profile_out(doc: dict) -> dict:
    out = {
        "id": str(doc["_id"]),
        "visibility": doc.get("visibility", "private"),
        "createdAt": to_iso(doc["created_at"]),
        "updatedAt": to_iso(doc["updated_at"]),
    }
    for name in SECTION_KEYS:
        out[name] = doc.get(name)
    return out


def _check_resume_ownership(user_id, sections: dict) -> None:
    career = sections.get("career")
    if isinstance(career, dict) and career.get("resumeId"):
        resume_id = career["resumeId"]
        owned = None
        try:
            owned = resumes_repo.get_owned_active(user_id, resume_id)
        except Exception:
            owned = None
        if owned is None:
            raise ApiError(
                400,
                "validation_error",
                "The request data is invalid.",
                {"career/resumeId": ["Must reference your own non-deleted resume."]},
            )


class ProfileMeView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]

    @extend_schema(responses=ProfileOut, operation_id="profiles_me_get")
    def get(self, request):
        doc = profiles_repo.get_by_user(request.user.user_id)
        if doc is None:
            raise ApiError(404, "profile_not_found", "You do not have a profile yet.")
        return Response(_profile_out(doc))

    @extend_schema(request=ProfileOut, responses=ProfileOut, operation_id="profiles_me_put")
    def put(self, request):
        sections, visibility, errors = ProfileBodyValidator(
            request.data, request.user.email
        ).validate()
        if errors:
            raise ApiError(400, "validation_error", "The request data is invalid.", errors)
        _check_resume_ownership(request.user.user_id, sections)

        doc, created, changed = profiles_repo.upsert(request.user.user_id, sections, visibility)
        emit_event(
            "profile.updated",
            "profile",
            doc["_id"],
            {"user_id": str(doc["user_id"]), "sections": changed},
        )
        return Response(_profile_out(doc), status=201 if created else 200)

    @extend_schema(request=ProfileOut, responses=ProfileOut, operation_id="profiles_me_patch")
    def patch(self, request):
        if profiles_repo.get_by_user(request.user.user_id) is None:
            raise ApiError(404, "profile_not_found", "You do not have a profile yet.")

        sections, visibility, errors = ProfileBodyValidator(
            request.data, request.user.email
        ).validate()
        if errors:
            raise ApiError(400, "validation_error", "The request data is invalid.", errors)
        _check_resume_ownership(request.user.user_id, sections)

        doc, changed = profiles_repo.replace_sections(request.user.user_id, sections, visibility)
        emit_event(
            "profile.updated",
            "profile",
            doc["_id"],
            {"user_id": str(doc["user_id"]), "sections": changed},
        )
        return Response(_profile_out(doc))


class ProfileSharedView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]

    @extend_schema(responses=SharedProfileOut, operation_id="profiles_me_shared")
    def get(self, request):
        p = profiles_repo.get_by_user(request.user.user_id)
        if p is None:
            raise ApiError(404, "profile_not_found", "You do not have a profile yet.")
        doc = {
            "schemaVersion": "1.0",
            "profileId": str(p["_id"]),
            "userId": str(p["user_id"]),
            "personal": p.get("personal", {}),
            "academic": p.get("academic", []),
            "certifications": p.get("certifications", []),
            "achievements": p.get("achievements", []),
            "career": p.get("career", {"skills": []}),
            "jobPreferences": p.get("jobPreferences", {}),
            "updatedAt": to_iso(p["updated_at"]),
        }
        if not FULL.is_valid(doc):
            logger.error(
                "Exported profile failed contract validation: %s",
                [e.message for e in FULL.iter_errors(doc)],
            )
            raise ApiError(500, "internal_error", "Profile export is invalid.")
        return Response(doc)


def _public_view(doc: dict) -> dict:
    personal = doc.get("personal", {}) or {}
    academic = []
    for rec in doc.get("academic", []) or []:
        academic.append(
            {
                k: rec[k]
                for k in (
                    "institution",
                    "program",
                    "degree",
                    "major",
                    "minor",
                    "startDate",
                    "graduationDate",
                    "status",
                )
                if k in rec
            }
        )
    career = doc.get("career", {}) or {}
    return {
        "id": str(doc["_id"]),
        "visibility": "public",
        "personal": {k: personal[k] for k in ("fullName", "location") if k in personal},
        "academic": academic,
        "certifications": doc.get("certifications", []),
        "achievements": doc.get("achievements", []),
        "career": {
            k: career[k]
            for k in ("headline", "summary", "skills", "experience", "projects")
            if k in career
        },
    }


class ProfilePublicView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=ProfileOut, operation_id="profiles_public_get")
    def get(self, request, user_id):
        target = parse_object_id(user_id)
        doc = profiles_repo.get_by_user(target)
        caller = request.user
        is_owner = caller.user_id == str(target)
        is_admin = caller.role == "admin"

        if doc is None:
            raise ApiError(404, "not_found", "Resource not found.")
        if is_owner or is_admin:
            return Response(_profile_out(doc))
        if doc.get("visibility") == "public":
            return Response(_public_view(doc))
        raise ApiError(404, "not_found", "Resource not found.")


profile_me = ProfileMeView.as_view()
profile_shared = ProfileSharedView.as_view()
profile_public = ProfilePublicView.as_view()
