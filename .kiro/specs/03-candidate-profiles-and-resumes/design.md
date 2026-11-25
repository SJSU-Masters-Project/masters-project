# Design: candidate profiles and resumes

## The contract (`backend/contracts/`)
- `shared-user-profile.v1.schema.json` and `shared-user-profile.v1.example.json` are Eshan's
  files from 2026-10-09, committed unchanged. Never edit them by hand; a new version is a new file.
- `api/contracts.py` loads the schema once and builds validators:
  ```python
  SCHEMA = json.loads((CONTRACTS_DIR / "shared-user-profile.v1.schema.json").read_text())
  FULL = Draft202012Validator(SCHEMA, format_checker=FormatChecker())
  SECTION = {name: Draft202012Validator(SCHEMA["properties"][name], format_checker=FormatChecker())
             for name in ("personal", "academic", "certifications", "achievements", "career", "jobPreferences")}
  def section_errors(name, value) -> dict[str, list[str]]   # {"academic/0/gpa": ["..."]}
  ```
  Section sub-schemas have no `$ref`, so validating each one on its own is exact.
  Format checks need the `jsonschema[format-nongpl]` extra (verified 2026-10-25: Eshan's
  example passes; a profile with empty arrays passes; bad email, URI, date-time and unknown
  fields are rejected with paths).

## profiles collection
```json
{ "_id": ObjectId, "user_id": ObjectId, "visibility": "private",
  "personal": {...}, "academic": [...], "certifications": [...], "achievements": [...],
  "career": {"skills": [...], ...}, "jobPreferences": {...},
  "section_updated_at": {"personal": ISODate, "career": ISODate, ...},
  "created_at": ISODate, "updated_at": ISODate }
```
Sections are stored exactly in contract shape. `section_updated_at` is careers-internal; it is
there so conflict handling in a later sync has per-section times to compare.
Index: `IndexModel([("user_id", 1)], unique=True, name="user_unique")`.

## Profile endpoints

| Method and path | Who | Behaviour |
|---|---|---|
| PUT `/api/v1/profiles/me` | candidate | upsert whole profile; fill defaults; 201 or 200 |
| PATCH `/api/v1/profiles/me` | candidate | replace listed sections only; 404 if none |
| GET `/api/v1/profiles/me` | candidate | full profile |
| GET `/api/v1/profiles/me/shared` | candidate | contract export |
| GET `/api/v1/profiles/{userId}` | authenticated | owner/admin full; others public view if public; else 404 |

Request body (PUT and PATCH):
`{"visibility": "public", "personal": {...}, "academic": [...], ..., "jobPreferences": {...}}`.
Unknown top-level keys give 400. Validation: for each present section call `section_errors`;
merge all errors into one 400 `validation_error`. Then check `career.resumeId` ownership.

Response: `{"id", "visibility", "createdAt", "updatedAt", <six sections>}`.

Export (`/shared`):
```python
{"schemaVersion": "1.0", "profileId": str(p["_id"]), "userId": str(p["user_id"]),
 <six sections>, "updatedAt": to_iso(p["updated_at"])}
```
Assert `FULL.is_valid(doc)` before returning; if it is not valid, log the errors and return
500 (this means a bug, because every section was validated on write).

## Public view (proposed; confirm with the team)
Returned to other signed-in users only when `visibility` is `public`:
- `personal`: `fullName`, `location` (no email, no phone)
- `academic[]`: `institution`, `program`, `degree`, `major`, `minor`, `startDate`, `graduationDate`, `status` (no `studentId`, `gpa`, `gpaScale`)
- `certifications`, `achievements`: as stored
- `career`: `headline`, `summary`, `skills`, `experience`, `projects` (no `resumeId`)
- `jobPreferences`: not included
Prof. Dhar asked for LinkedIn-like public profiles on 2026-09-30; which fields count as
public was not discussed, so this list is the backend's proposal.

## resumes collection
```json
{ "_id": ObjectId, "user_id": ObjectId, "filename": "jordan_lee_resume.pdf",
  "content_type": "application/pdf", "size_bytes": 182344, "sha256": "ab12...",
  "storage": {"backend": "local", "key": "resumes/<user_id>/<resume_id>.pdf"},
  "text": "....", "text_status": "done", "text_chars": 5321,
  "created_at": ISODate, "deleted_at": null }
```
Indexes: `[("user_id", 1), ("deleted_at", 1), ("created_at", -1)]` named `user_active`, and
`[("user_id", 1), ("sha256", 1)]` named `user_sha`.

## Upload pipeline (`POST /api/v1/resumes`, `parser_classes = [MultiPartParser]`)
1. `file = request.FILES.get("file")`; missing gives 400.
2. `file.size > 5 * 1024 * 1024` gives 413 `file_too_large` (checked before reading content).
3. Read the bytes. Sniff the type:
   - PDF: starts with `b"%PDF-"`.
   - DOCX: `zipfile.is_zipfile`, contains `word/document.xml`, and the sum of `ZipInfo.file_size`
     is at most 50 MB (guards against zip bombs).
   - Anything else gives 415 `unsupported_file_type`.
4. Count the user's non-deleted resumes; 10 or more gives 409 `resume_limit`.
5. `sha256`; an existing non-deleted resume with the same hash gives 409 `duplicate_resume`.
6. Generate `_id` first, write the file to storage under key `resumes/<user_id>/<_id>.<pdf|docx>`,
   then insert the document. If the insert fails, delete the stored file.
7. Extract text (below), update `text`, `text_status`, `text_chars`.
8. `emit_event("resume.uploaded", "resume", _id, {"user_id": ..., "text_status": ...})`.

Filename: `os.path.basename`, strip control characters, cut to 200 characters; the stored key
never uses it.

## Text extraction (`api/text_extract.py`)
- PDF: `pypdf.PdfReader(BytesIO(data))`; encrypted files give `failed`; read at most 50 pages;
  join `page.extract_text() or ""`.
- DOCX: `docx.Document(BytesIO(data))`; join paragraph text and table cell text.
- Normalise whitespace, cap at 200,000 characters. Empty result gives `empty`; any exception
  gives `failed` (log it). Extraction never raises to the view.
- Scanned PDFs (images only) give `empty`. OCR is out of scope; note it for the extraction owner.

## Storage (`api/storage.py`)
```python
class ResumeStorage(Protocol):
    def save(self, key: str, data: bytes, content_type: str) -> None: ...
    def open(self, key: str) -> BinaryIO: ...
    def delete(self, key: str) -> None: ...
def get_storage() -> ResumeStorage    # chosen by settings.RESUME_STORAGE
```
- `LocalStorage(root=settings.RESUME_LOCAL_ROOT)`: resolves `root / key` and refuses any path
  outside `root`. Default root `backend/var/` (git-ignored).
- `S3Storage(bucket, region)`: boto3 `put_object(..., ServerSideEncryption="AES256")`,
  `get_object`, `delete_object`. Install boto3 only in this task. The bucket is a request to
  Prof. Dhar (spec 06); until it exists production uses local storage on the instance.
- Settings: `RESUME_STORAGE` (`local` | `s3`), `RESUME_LOCAL_ROOT`, `RESUME_S3_BUCKET`, `RESUME_S3_REGION`.
Why not MongoDB or GridFS: the Atlas free tier holds 512 MB, which a few hundred resumes would use up.

## Other resume endpoints

| Method and path | Who | Behaviour |
|---|---|---|
| GET `/api/v1/resumes` | candidate | own, non-deleted, newest first, paginated; no `text` |
| GET `/api/v1/resumes/{id}` | owner | metadata plus `text_status`, `text_chars` |
| GET `/api/v1/resumes/{id}/download` | owner | `FileResponse`, `as_attachment=True`, stored content type |
| DELETE `/api/v1/resumes/{id}` | owner | delete file, set `deleted_at`, unset `career.resumeId` if equal, event, 204 |

Non-owners get 404 for all of these. Employer access arrives with matches in spec 05.

## Deployment notes for spec 06
- nginx `client_max_body_size 6m;` on the `/api/` location (file limit 5 MB plus form overhead).
- Django `FILE_UPLOAD_MAX_MEMORY_SIZE` stays at its 2.5 MB default; bigger files go to a temp file.
