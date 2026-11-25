# Requirements Document

## Introduction

Employers create a company and post jobs; anyone can browse open jobs. Each job lists its
skills, each marked required or optional, and its number of openings, which the allocation
engine later uses as the employer's capacity. This replaces the placeholder `GET /api/jobs/`.
Builds on spec 01 (errors, ids, paging, dev auth, roles, indexes, events).

## Requirements

### Requirement 1: Companies

**User Story:** As an employer, I want to create my company, so that the jobs I post show who is hiring.

#### Acceptance Criteria
1. WHEN an employer posts `POST /api/v1/companies` with a valid `name` (2 to 150 characters) and optional `website` (URL), `description` (up to 5,000 characters) and `location` (up to 200 characters) THEN THE SYSTEM SHALL create the company with the caller as its only member and return 201 with the company.
2. IF the employer is already a member of a company THEN THE SYSTEM SHALL return 409 with code `already_member`.
3. WHEN a candidate or admin posts to `/api/v1/companies` THEN THE SYSTEM SHALL return 403.
4. WHEN any authenticated user requests `GET /api/v1/companies/{id}` THEN THE SYSTEM SHALL return the company's `id`, `name`, `website`, `description`, `location` and `created_at`, and SHALL NOT return member ids.
5. WHEN a member sends `PATCH /api/v1/companies/{id}` THEN THE SYSTEM SHALL update the given fields; WHEN a non-member sends it THEN THE SYSTEM SHALL return 403.
6. WHEN a company's `name` changes THEN THE SYSTEM SHALL update the company name shown on all its jobs.
7. WHEN an employer requests `GET /api/v1/companies/mine` THEN THE SYSTEM SHALL return their company, or 404 with code `no_company`.

### Requirement 2: Create a job

**User Story:** As an employer, I want to draft a job with its skills and openings, so that
the platform can match candidates to it.

#### Acceptance Criteria
1. WHEN an employer with a company posts `POST /api/v1/jobs` with valid fields THEN THE SYSTEM SHALL create the job in status `draft` for that company and return 201.
2. THE SYSTEM SHALL require `title` (3 to 150 characters), `description` (50 to 20,000 characters), `location` (up to 200 characters), `work_mode` (`on_site`, `hybrid` or `remote`), `employment_type` (`full_time`, `part_time`, `internship`, `contract` or `co_op`), `skills` and `openings`.
3. THE SYSTEM SHALL require `skills` to hold 1 to 50 items, each with `name` (1 to 100 characters) and boolean `required`, with names unique ignoring case, and at least one item with `required` true.
4. THE SYSTEM SHALL require `openings` to be a whole number from 1 to 100.
5. IF the employer has no company THEN THE SYSTEM SHALL return 409 with code `no_company`.
6. WHEN a candidate posts to `/api/v1/jobs` THEN THE SYSTEM SHALL return 403.

### Requirement 3: Edit a job

**User Story:** As an employer, I want to correct a job, so that matching uses accurate requirements.

#### Acceptance Criteria
1. WHEN a member of the job's company sends `PATCH /api/v1/jobs/{id}` on a `draft` or `open` job THEN THE SYSTEM SHALL validate and apply the given fields with the rules of Requirement 2.
2. IF the job is `closed` THEN THE SYSTEM SHALL return 409 with code `invalid_state`.
3. WHEN a user who is not a member of the job's company sends the PATCH THEN THE SYSTEM SHALL return 404 for draft or closed jobs and 403 for open jobs.
4. WHEN an `open` job is changed THEN THE SYSTEM SHALL emit a `job.updated` event.

### Requirement 4: Job lifecycle

**User Story:** As an employer, I want to publish and close jobs, so that candidates only see roles that are hiring.

#### Acceptance Criteria
1. WHEN a member posts `POST /api/v1/jobs/{id}/publish` on a `draft` job THEN THE SYSTEM SHALL set status `open`, set `published_at`, emit `job.published` and return the job.
2. WHEN a member posts `POST /api/v1/jobs/{id}/close` on an `open` job THEN THE SYSTEM SHALL set status `closed`, set `closed_at`, emit `job.closed` and return the job.
3. IF any other status change is requested THEN THE SYSTEM SHALL return 409 with code `invalid_state` and the current status in `details`.

### Requirement 5: Browse open jobs

**User Story:** As a candidate or visitor, I want to search open jobs, so that I can find roles that fit me.

#### Acceptance Criteria
1. WHEN anyone, signed in or not, requests `GET /api/v1/jobs` THEN THE SYSTEM SHALL return only `open` jobs, newest `published_at` first, paginated as in spec 01.
2. WHEN `q` is given THEN THE SYSTEM SHALL return open jobs matching it in title, skills or description, most relevant first.
3. WHEN `work_mode`, `employment_type`, `skill`, `location` or `company_id` is given THEN THE SYSTEM SHALL filter by it; `skill` matches a skill name ignoring case and `location` matches a substring ignoring case.
4. WHEN anyone requests `GET /api/v1/jobs/{id}` for an `open` job THEN THE SYSTEM SHALL return it.
5. WHEN a non-member requests a `draft` or `closed` job THEN THE SYSTEM SHALL return 404; members and admins SHALL see it.

### Requirement 6: Company job list

**User Story:** As an employer, I want to see all my company's jobs, so that I can manage drafts and closed roles.

#### Acceptance Criteria
1. WHEN a member or admin requests `GET /api/v1/companies/{id}/jobs` THEN THE SYSTEM SHALL return jobs in every status, filterable by `status`.
2. WHEN anyone else requests it THEN THE SYSTEM SHALL return only the company's `open` jobs.

### Requirement 7: Job representation

**User Story:** As a frontend developer, I want one job shape everywhere, so that list and detail views share code.

#### Acceptance Criteria
1. THE SYSTEM SHALL return each job as `id`, `company` (`id`, `name`), `title`, `description`, `location`, `work_mode`, `employment_type`, `skills` (`name`, `required`), `openings`, `status`, `published_at`, `closed_at`, `created_at`, `updated_at`.
2. THE SYSTEM SHALL return skills in the order the employer gave them.
