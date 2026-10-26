import hashlib
import os
import re

from django.http import FileResponse
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.errors import ApiError
from api.events import emit_event
from api.ids import parse_object_id
from api.pagination import page_response, parse_page_params
from api.permissions import IsCandidate
from api.repositories import profiles as profiles_repo
from api.repositories import resumes as resumes_repo
from api.serializers.resumes import ResumeDetailOut, ResumeListOut, ResumeOut, ResumeUploadIn
from api.storage import get_storage
from api.text_extract import extract_text, sniff_type
from api.timeutils import to_iso, utcnow

MAX_SIZE = 5 * 1024 * 1024
_CONTENT_TYPE = {
    "pdf": "application/pdf",
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
}


def _clean_filename(name: str) -> str:
    base = os.path.basename(name or "resume")
    base = re.sub(r"[\x00-\x1f]", "", base)
    return base[:200] or "resume"


def _resume_out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "filename": doc["filename"],
        "content_type": doc["content_type"],
        "size_bytes": doc["size_bytes"],
        "text_status": doc["text_status"],
        "created_at": to_iso(doc["created_at"]),
    }


class ResumesView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]
    parser_classes = [MultiPartParser]

    @extend_schema(responses=ResumeListOut, operation_id="resumes_list")
    def get(self, request):
        page = parse_page_params(request.query_params)
        docs, total = resumes_repo.list_active(request.user.user_id, page)
        items = [_resume_out(d) for d in docs]
        return Response(page_response(items, total, page))

    @extend_schema(
        request=ResumeUploadIn, responses={201: ResumeOut}, operation_id="resumes_create"
    )
    def post(self, request):
        user_id = request.user.user_id
        file = request.FILES.get("file")
        if file is None:
            raise ApiError(400, "validation_error", "A file is required.", {"file": ["Required."]})

        # Step 2: size check before reading content.
        if file.size > MAX_SIZE:
            raise ApiError(413, "file_too_large", "The file exceeds 5 MB.")

        data = file.read()

        # Step 3: sniff type by content.
        file_type = sniff_type(data)
        if file_type is None:
            raise ApiError(415, "unsupported_file_type", "Only PDF and DOCX files are accepted.")

        # Step 4: per-user limit.
        if resumes_repo.at_limit(user_id):
            raise ApiError(409, "resume_limit", "You already have the maximum of 10 resumes.")

        # Step 5: duplicate by content hash.
        sha256 = hashlib.sha256(data).hexdigest()
        dup = resumes_repo.find_active_by_hash(user_id, sha256)
        if dup is not None:
            raise ApiError(
                409,
                "duplicate_resume",
                "You already uploaded this file.",
                {"id": str(dup["_id"])},
            )

        # Step 6: write file first, then insert; roll back file on insert failure.
        rid = resumes_repo.new_id()
        uid = parse_object_id(user_id)
        key = f"resumes/{uid}/{rid}.{file_type}"
        content_type = _CONTENT_TYPE[file_type]
        storage = get_storage()
        storage.save(key, data, content_type)

        from django.conf import settings

        doc = {
            "_id": rid,
            "user_id": uid,
            "filename": _clean_filename(file.name),
            "content_type": content_type,
            "size_bytes": len(data),
            "sha256": sha256,
            "storage": {"backend": settings.RESUME_STORAGE, "key": key},
            "text": "",
            "text_status": "pending",
            "text_chars": 0,
            "created_at": utcnow(),
            "deleted_at": None,
        }
        try:
            resumes_repo.insert(doc)
        except Exception:
            storage.delete(key)
            raise

        # Step 7: extract text (never raises to the view).
        text, status = extract_text(data, file_type)
        resumes_repo.update_text(rid, text, status, len(text))
        doc["text_status"] = status

        # Step 8: event.
        emit_event(
            "resume.uploaded",
            "resume",
            rid,
            {"user_id": str(uid), "text_status": status},
        )
        return Response(_resume_out(doc), status=201)


class ResumeDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]

    @extend_schema(responses=ResumeDetailOut, operation_id="resumes_retrieve")
    def get(self, request, resume_id):
        doc = resumes_repo.get_owned_active(request.user.user_id, resume_id)
        if doc is None:
            raise ApiError(404, "not_found", "Resource not found.")
        out = _resume_out(doc)
        out["text_chars"] = doc.get("text_chars", 0)
        return Response(out)

    @extend_schema(responses={204: None}, operation_id="resumes_delete")
    def delete(self, request, resume_id):
        doc = resumes_repo.get_owned_active(request.user.user_id, resume_id)
        if doc is None:
            raise ApiError(404, "not_found", "Resource not found.")
        get_storage().delete(doc["storage"]["key"])
        resumes_repo.soft_delete(resume_id)
        profiles_repo.unset_resume_id_if(request.user.user_id, str(doc["_id"]))
        emit_event("resume.deleted", "resume", doc["_id"], {"user_id": str(doc["user_id"])})
        return Response(status=204)


class ResumeDownloadView(APIView):
    permission_classes = [IsAuthenticated, IsCandidate]

    @extend_schema(
        responses={(200, "application/octet-stream"): bytes}, operation_id="resumes_download"
    )
    def get(self, request, resume_id):
        doc = resumes_repo.get_owned_active(request.user.user_id, resume_id)
        if doc is None:
            raise ApiError(404, "not_found", "Resource not found.")
        fh = get_storage().open(doc["storage"]["key"])
        return FileResponse(
            fh,
            as_attachment=True,
            filename=doc["filename"],
            content_type=doc["content_type"],
        )


resumes = ResumesView.as_view()
resume_detail = ResumeDetailView.as_view()
resume_download = ResumeDownloadView.as_view()
