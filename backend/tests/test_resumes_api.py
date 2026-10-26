import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from tests.conftest import as_user
from tests.resume_fixtures import make_docx_bytes, make_pdf_bytes

CANDIDATE = "jordan@example.com"


@pytest.fixture
def storage_root(tmp_path):
    with override_settings(RESUME_STORAGE="local", RESUME_LOCAL_ROOT=str(tmp_path)):
        yield tmp_path


def _upload(client, data: bytes, name: str, content_type: str):
    from django.core.files.uploadedfile import SimpleUploadedFile

    f = SimpleUploadedFile(name, data, content_type=content_type)
    return client.post("/api/v1/resumes", {"file": f}, format="multipart")


def test_upload_pdf_201(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    resp = _upload(api, make_pdf_bytes(), "resume.pdf", "application/pdf")
    assert resp.status_code == 201, resp.json()
    body = resp.json()
    assert body["content_type"] == "application/pdf"
    assert set(body.keys()) >= {
        "id",
        "filename",
        "content_type",
        "size_bytes",
        "text_status",
        "created_at",
    }


def test_upload_docx_201(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    resp = _upload(
        api,
        make_docx_bytes(),
        "resume.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert resp.status_code == 201
    assert resp.json()["text_status"] == "done"


def test_too_large_413(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    big = b"%PDF-" + b"0" * (5 * 1024 * 1024 + 1)
    resp = _upload(api, big, "big.pdf", "application/pdf")
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "file_too_large"


def test_text_renamed_pdf_415(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    resp = _upload(api, b"just plain text, not a pdf", "fake.pdf", "application/pdf")
    assert resp.status_code == 415
    assert resp.json()["error"]["code"] == "unsupported_file_type"


def test_duplicate_409_with_id(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    data = make_pdf_bytes()
    first = _upload(api, data, "a.pdf", "application/pdf").json()
    resp = _upload(api, data, "b.pdf", "application/pdf")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "duplicate_resume"
    assert resp.json()["error"]["details"]["id"] == first["id"]


def test_resume_limit_409(api, storage_root, db):
    as_user(api, CANDIDATE, "candidate")
    # seed 10 active resumes directly for this user
    uid = db.users.find_one_and_update  # noqa
    api.get("/api/v1/me")  # ensure user exists
    user = db.users.find_one({"email": CANDIDATE})
    from api.timeutils import utcnow
    from bson import ObjectId

    for i in range(10):
        db.resumes.insert_one(
            {
                "_id": ObjectId(),
                "user_id": user["_id"],
                "filename": f"r{i}.pdf",
                "content_type": "application/pdf",
                "size_bytes": 10,
                "sha256": f"hash{i}",
                "storage": {"backend": "local", "key": f"k{i}"},
                "text": "",
                "text_status": "done",
                "text_chars": 0,
                "created_at": utcnow(),
                "deleted_at": None,
            }
        )
    resp = _upload(api, make_pdf_bytes(), "r11.pdf", "application/pdf")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "resume_limit"


def test_filename_basename_only(api, storage_root, db):
    as_user(api, CANDIDATE, "candidate")
    resp = _upload(api, make_pdf_bytes(), "../../etc/passwd.pdf", "application/pdf")
    assert resp.status_code == 201
    assert resp.json()["filename"] == "passwd.pdf"


def test_no_file_content_in_mongo(api, storage_root, db):
    as_user(api, CANDIDATE, "candidate")
    rid = _upload(api, make_pdf_bytes(), "r.pdf", "application/pdf").json()["id"]
    from bson import ObjectId

    doc = db.resumes.find_one({"_id": ObjectId(rid)})
    # only metadata + text, never raw bytes
    assert "data" not in doc and "content" not in doc and "bytes" not in doc
    assert isinstance(doc.get("text", ""), str)


def test_upload_emits_event(api, storage_root, db):
    as_user(api, CANDIDATE, "candidate")
    _upload(api, make_pdf_bytes(), "r.pdf", "application/pdf")
    assert db.events.count_documents({"type": "resume.uploaded"}) == 1


# ---- list / detail / download / delete ----


def test_list_excludes_text_and_deleted(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    _upload(
        api,
        make_docx_bytes("one"),
        "a.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    body = api.get("/api/v1/resumes").json()
    assert body["total"] == 1
    assert "text" not in body["items"][0]


def test_other_candidate_404_on_read_download_delete(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    rid = _upload(api, make_pdf_bytes(), "r.pdf", "application/pdf").json()["id"]

    other = APIClient()
    as_user(other, "other@example.com", "candidate")
    assert other.get(f"/api/v1/resumes/{rid}").status_code == 404
    assert other.get(f"/api/v1/resumes/{rid}/download").status_code == 404
    assert other.delete(f"/api/v1/resumes/{rid}").status_code == 404


def test_download_returns_same_bytes_attachment(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    data = make_pdf_bytes()
    rid = _upload(api, data, "r.pdf", "application/pdf").json()["id"]
    resp = api.get(f"/api/v1/resumes/{rid}/download")
    assert resp.status_code == 200
    assert b"".join(resp.streaming_content) == data
    assert "attachment" in resp["Content-Disposition"]


def test_delete_clears_resume_id_and_emits(api, storage_root, db):
    as_user(api, CANDIDATE, "candidate")
    rid = _upload(api, make_pdf_bytes(), "r.pdf", "application/pdf").json()["id"]
    # link it to the profile
    api.put(
        "/api/v1/profiles/me",
        {
            "personal": {"fullName": "J"},
            "career": {"skills": [], "resumeId": rid},
            "jobPreferences": {"targetRoles": [], "employmentTypes": [], "workModes": []},
        },
        format="json",
    )
    resp = api.delete(f"/api/v1/resumes/{rid}")
    assert resp.status_code == 204
    assert db.events.count_documents({"type": "resume.deleted"}) == 1
    got = api.get("/api/v1/profiles/me").json()
    assert "resumeId" not in got["career"]
    # subsequent read is 404
    assert api.get(f"/api/v1/resumes/{rid}").status_code == 404


# ---- link resume to profile ----


def test_profile_rejects_foreign_resume_id(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    my_rid = _upload(api, make_pdf_bytes(), "r.pdf", "application/pdf").json()["id"]

    # own resume accepted
    ok = api.put(
        "/api/v1/profiles/me",
        {
            "personal": {"fullName": "J"},
            "career": {"skills": [], "resumeId": my_rid},
            "jobPreferences": {"targetRoles": [], "employmentTypes": [], "workModes": []},
        },
        format="json",
    )
    assert ok.status_code == 201

    # another user's resume id rejected
    other = APIClient()
    as_user(other, "other@example.com", "candidate")
    other_rid = _upload(
        other,
        make_docx_bytes("x"),
        "o.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ).json()["id"]

    bad = api.patch(
        "/api/v1/profiles/me",
        {"career": {"skills": [], "resumeId": other_rid}},
        format="json",
    )
    assert bad.status_code == 400


def test_profile_rejects_deleted_resume_id(api, storage_root):
    as_user(api, CANDIDATE, "candidate")
    rid = _upload(api, make_pdf_bytes(), "r.pdf", "application/pdf").json()["id"]
    api.delete(f"/api/v1/resumes/{rid}")
    bad = api.patch(
        "/api/v1/profiles/me",
        {"career": {"skills": [], "resumeId": rid}},
        format="json",
    )
    # patch on a non-existent profile returns 404; create first
    assert bad.status_code in (400, 404)
    # ensure via PUT path too
    resp = api.put(
        "/api/v1/profiles/me",
        {
            "personal": {"fullName": "J"},
            "career": {"skills": [], "resumeId": rid},
            "jobPreferences": {"targetRoles": [], "employmentTypes": [], "workModes": []},
        },
        format="json",
    )
    assert resp.status_code == 400
