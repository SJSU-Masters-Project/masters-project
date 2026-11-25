# Requirements Document

## Introduction

Candidates keep one careers profile and upload resumes. The profile uses the shared profile
schema v1.0 (Eshan, 2026-10-09; file in `backend/contracts/`) as its shape, so it can later be
exported for MyAcademic sync without conversion. Resume files are stored outside MongoDB, and
their text is extracted at upload for the skill extraction service. Sync itself, and employer
access to resumes, are out of scope (spec 05). Builds on spec 01.

Exception to the API naming rule: profile endpoints use the contract's camelCase field names,
because their body is the contract shape.

## Requirements

### Requirement 1: Create and replace a profile

**User Story:** As a candidate, I want to save my profile, so that the platform can match me to jobs.

#### Acceptance Criteria
1. WHEN a candidate sends `PUT /api/v1/profiles/me` with valid sections THEN THE SYSTEM SHALL create or replace their profile and return it (201 on create, 200 on replace).
2. THE SYSTEM SHALL validate each section (`personal`, `academic`, `certifications`, `achievements`, `career`, `jobPreferences`) against the matching section of `shared-user-profile.v1.schema.json`, including formats (email, URI, date, date-time).
3. THE SYSTEM SHALL require `personal.fullName`; WHEN `personal.email` is missing THEN THE SYSTEM SHALL use the candidate's account email.
4. WHEN optional sections are missing THEN THE SYSTEM SHALL store them empty (`[]` for lists; `{"skills": []}` for `career`; empty `targetRoles`, `employmentTypes` and `workModes` for `jobPreferences`).
5. IF the body contains a field the contract does not define THEN THE SYSTEM SHALL return 400 with the field path in `details`.
6. WHEN an employer or admin sends the PUT THEN THE SYSTEM SHALL return 403.

### Requirement 2: Update parts of a profile

**User Story:** As a candidate, I want to change one section at a time, so that I do not resend my whole profile.

#### Acceptance Criteria
1. WHEN a candidate sends `PATCH /api/v1/profiles/me` with one or more sections THEN THE SYSTEM SHALL replace exactly those sections after validating them and leave the others unchanged.
2. IF the candidate has no profile THEN THE SYSTEM SHALL return 404 with code `profile_not_found`.
3. WHEN `career.resumeId` is set THEN THE SYSTEM SHALL check that it names a non-deleted resume owned by the candidate, else return 400.
4. WHEN a profile is created or changed THEN THE SYSTEM SHALL record the update time of each changed section and emit `profile.updated` with the changed section names.

### Requirement 3: Read my profile

**User Story:** As a candidate, I want to read my profile, so that the portal can show and edit it.

#### Acceptance Criteria
1. WHEN a candidate requests `GET /api/v1/profiles/me` THEN THE SYSTEM SHALL return `id`, `visibility`, `createdAt`, `updatedAt` and all six sections.
2. IF no profile exists THEN THE SYSTEM SHALL return 404 with code `profile_not_found`.

### Requirement 4: Contract export

**User Story:** As the team member building sync, I want the profile in the exact contract
shape, so that MyAcademic receives valid data.

#### Acceptance Criteria
1. WHEN a candidate requests `GET /api/v1/profiles/me/shared` THEN THE SYSTEM SHALL return a document with `schemaVersion` "1.0", `profileId`, `userId`, the six sections and `updatedAt`.
2. THE exported document SHALL validate against the full shared schema; a test SHALL check this for a minimal and a full profile.
3. THE exported document SHALL NOT contain `visibility` or any other careers-only field.

### Requirement 5: Profile visibility

**User Story:** As a candidate, I want to choose whether other signed-in users can see my
profile, so that I control my exposure.

#### Acceptance Criteria
1. THE SYSTEM SHALL store `visibility` as `private` or `public`, defaulting to `private`, settable through PUT or PATCH.
2. WHEN an authenticated user requests `GET /api/v1/profiles/{userId}` for another user's `public` profile THEN THE SYSTEM SHALL return the public view only (see design.md "Public view").
3. WHEN the profile is `private` or does not exist THEN THE SYSTEM SHALL return 404 to everyone except its owner and admins.
4. WHEN the owner or an admin requests it THEN THE SYSTEM SHALL return the full profile.

### Requirement 6: Upload a resume

**User Story:** As a candidate, I want to upload my resume, so that my skills can be extracted from it.

#### Acceptance Criteria
1. WHEN a candidate posts `POST /api/v1/resumes` as `multipart/form-data` with field `file` THEN THE SYSTEM SHALL store the file and return 201 with `id`, `filename`, `content_type`, `size_bytes`, `text_status` and `created_at`.
2. IF the file is larger than 5 MB THEN THE SYSTEM SHALL return 413 with code `file_too_large`.
3. IF the file content is not a PDF or a DOCX, judged by its bytes and not by its name or declared type, THEN THE SYSTEM SHALL return 415 with code `unsupported_file_type`.
4. IF the candidate already has 10 resumes THEN THE SYSTEM SHALL return 409 with code `resume_limit`.
5. IF the candidate already has a resume with identical content THEN THE SYSTEM SHALL return 409 with code `duplicate_resume` and the existing id in `details`.
6. THE SYSTEM SHALL keep only the base name of the uploaded filename, at most 200 characters.
7. THE SYSTEM SHALL NOT store file contents in MongoDB.
8. WHEN a resume is stored THEN THE SYSTEM SHALL emit `resume.uploaded`.

### Requirement 7: Resume text

**User Story:** As the owner of the skill extraction service, I want plain text for each resume, so that extraction does not parse files.

#### Acceptance Criteria
1. WHEN a resume is uploaded THEN THE SYSTEM SHALL extract its text and set `text_status` to `done`, `empty` (no text found) or `failed`.
2. IF extraction fails THEN THE SYSTEM SHALL still store the resume and return 201.
3. THE SYSTEM SHALL keep at most 200,000 characters of text per resume.
4. THE extracted text SHALL NOT appear in list responses.

### Requirement 8: Manage resumes

**User Story:** As a candidate, I want to list, download and delete my resumes, so that I control what the platform holds.

#### Acceptance Criteria
1. WHEN a candidate requests `GET /api/v1/resumes` THEN THE SYSTEM SHALL return their non-deleted resumes, newest first.
2. WHEN the owner requests `GET /api/v1/resumes/{id}/download` THEN THE SYSTEM SHALL return the file with its content type and an attachment filename.
3. WHEN anyone other than the owner requests a resume or its file THEN THE SYSTEM SHALL return 404.
4. WHEN the owner sends `DELETE /api/v1/resumes/{id}` THEN THE SYSTEM SHALL delete the stored file, mark the record deleted, clear `career.resumeId` if it pointed to it, emit `resume.deleted` and return 204.

### Requirement 9: File storage

**User Story:** As the person deploying, I want local storage in development and encrypted S3 in production, so that the same code runs in both.

#### Acceptance Criteria
1. WHEN `RESUME_STORAGE` is `local` (the default) THEN THE SYSTEM SHALL store files under `RESUME_LOCAL_ROOT`.
2. WHEN `RESUME_STORAGE` is `s3` THEN THE SYSTEM SHALL store files in `RESUME_S3_BUCKET` with server-side encryption.
3. THE storage key SHALL contain only ids generated by the system, never user-supplied names.
