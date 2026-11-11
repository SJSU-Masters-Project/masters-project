# Implementation Plan

Prerequisite: spec 01 merged. Spec 02 is not required.

- [ ] 1. Commit the contract and its validators
  - Add `backend/contracts/shared-user-profile.v1.schema.json` and `shared-user-profile.v1.example.json` (Eshan's 2026-10-09 files, unchanged).
  - Write `api/contracts.py` per design.md "The contract".
  - Tests: the example passes `FULL`; a minimal profile with empty arrays passes; a bad email, bad URI, bad date-time and an unknown field each produce an error with the right path.
  - _Requirements: 1.2, 1.5, 4.2_

- [ ] 2. Profiles repository and indexes
  - Add the `profiles` index to `api/indexes.py`.
  - `api/repositories/profiles.py`: `get_by_user`, `upsert(user_id, sections, visibility)` filling defaults, `replace_sections(user_id, sections)` updating `section_updated_at` for those sections only, `set_resume_id`, `unset_resume_id_if(user_id, resume_id)`.
  - Unit tests: defaults filled; replacing one section leaves the others and their timestamps unchanged; unique `user_id`.
  - _Requirements: 1.1, 1.4, 2.1, 2.4_

- [ ] 3. PUT and GET for my profile
  - Serializers that run `section_errors` for each present section and reject unknown top-level keys; account email fills a missing `personal.email`.
  - Views: `PUT /profiles/me`, `GET /profiles/me`. Emit `profile.updated`.
  - Tests: 201 then 200; full example round-trips; missing `fullName` 400; unknown key 400 with path; employer 403; GET before create 404 `profile_not_found`; event lists changed sections.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.4, 3.1, 3.2_

- [ ] 4. PATCH my profile
  - View `PATCH /profiles/me` replacing only the given sections.
  - Tests: patch `career` only; patch before create 404; invalid section 400 and nothing saved; `visibility` change alone works.
  - _Requirements: 2.1, 2.2, 2.4, 5.1_

- [ ] 5. Contract export
  - View `GET /profiles/me/shared` per design.md, with the `FULL.is_valid` assertion.
  - Tests: minimal and full profiles export valid documents; `visibility` and `section_updated_at` are absent; ids are hex strings.
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 6. Public profile view
  - View `GET /profiles/{userId}` with the rules of Requirement 5 and the field list in design.md "Public view".
  - Tests: owner full; admin full; other user on public sees no email, phone, studentId, gpa, resumeId or jobPreferences; private gives 404; unknown user 404; anonymous 401.
  - _Requirements: 5.2, 5.3, 5.4_

- [ ] 7. Storage backends
  - `api/storage.py` with `LocalStorage` (path-escape guard) and `S3Storage` (SSE AES256); settings and `.env.example` entries; add `backend/var/` to `.gitignore`.
  - Tests: local save, open and delete; a key like `../x` is refused; S3 class tested with `unittest.mock` on the boto3 client (no network).
  - _Requirements: 9.1, 9.2, 9.3_

- [ ] 8. Type sniffing and text extraction
  - Add `pypdf` and `python-docx` to `requirements.txt`.
  - `api/text_extract.py` per design.md; `sniff_type(data) -> "pdf" | "docx" | None` with the zip-size guard.
  - Test fixtures generated in the test (a one-page PDF and a DOCX built with python-docx; for the PDF, a small byte string or a `pypdf` writer page): text found gives `done`; blank gives `empty`; corrupt bytes give `failed`; a `.pdf`-named PNG is rejected by sniffing; text over 200,000 characters is cut.
  - _Requirements: 6.3, 7.1, 7.2, 7.3_

- [ ] 9. Upload endpoint
  - Resumes indexes; `api/repositories/resumes.py`; `POST /resumes` following the 8 steps in design.md "Upload pipeline", with cleanup if the insert fails.
  - Tests: 201 for PDF and DOCX; 413 at 5 MB + 1 byte (check before reading); 415 for a text file renamed `.pdf`; 409 `resume_limit` on the 11th; 409 `duplicate_resume` with the existing id; filename `../../etc/passwd.pdf` is stored as `passwd.pdf`; nothing about the file goes into MongoDB except metadata and text; event emitted.
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 7.2_

- [ ] 10. List, read, download and delete
  - Views per design.md "Other resume endpoints".
  - Tests: list excludes `text` and deleted resumes; another candidate gets 404 on read, download and delete; download returns the same bytes and an attachment header; delete removes the file, clears `career.resumeId` when it matched, emits `resume.deleted`, returns 204.
  - _Requirements: 7.4, 8.1, 8.2, 8.3, 8.4_

- [ ] 11. Link resume to profile
  - Enforce Requirement 2.3 in PUT and PATCH: `career.resumeId` must be the caller's non-deleted resume.
  - Tests: own resume accepted; another user's resume id 400; deleted resume id 400.
  - _Requirements: 2.3_

- [ ] 12. OpenAPI and handover
  - `@extend_schema` for every view, including the multipart request for upload; `spectacular --validate --fail-on-warn` passes.
  - README "Profiles and resumes API" section with curl examples (upload uses `-F file=@resume.pdf`).
  - Tell Uday (skill extraction) about `resume.uploaded` events and the `resumes.text` field, and that scanned PDFs come through as `text_status: empty`.
  - _Requirements: 6.8, 7.1_
