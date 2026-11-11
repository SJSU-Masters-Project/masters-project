# Requirements Document

> **GATED.**
> Part A (Requirements 1 to 5) needs Gate B: each service owner agrees the shape of the
> collection their service writes (proposals in design.md). The repo's 2026-09-16 notes name
> the owners: skill extraction and fairness audit, Uday; knowledge graph, scorer and
> explanations, Himanshu; allocation engine, Eshan; screening interviewer, Nitish.
> Part B (Requirements 6 and 7) needs Gate C: the MyAcademic sync decisions.
> Requirement 6 (consent flag) and the read-only stub in Requirement 7 may be built before Gate C.

## Introduction

The React portal talks only to this API. The other project services read the `events`
outbox, do their work and write results to their own MongoDB collections; this API reads
those collections and serves them to candidates, employers and admins. This spec also adds
the integration stub for the advisor's MyAcademic platform (workbook requirement R11).

## Requirements

### Requirement 1: Candidate's job matches

**User Story:** As a candidate, I want to see jobs matched to me with a confidence level, so that I know where to apply.

#### Acceptance Criteria
1. WHEN a candidate requests `GET /api/v1/me/matches` THEN THE SYSTEM SHALL return open jobs from the latest completed scoring run, best first, each with `score`, `confidence_band` (`high`, `medium` or `low`) and `model`.
2. WHEN no completed run includes the candidate THEN THE SYSTEM SHALL return an empty list, not an error.
3. THE SYSTEM SHALL NOT return closed or draft jobs.

### Requirement 2: Employer's matched candidates

**User Story:** As an employer, I want to see candidates matched to my job, ranked or allocated, so that I can choose whom to screen.

#### Acceptance Criteria
1. WHEN a member of the job's company requests `GET /api/v1/jobs/{id}/matches?mode=ranked` THEN THE SYSTEM SHALL return candidates for that job from the latest completed scoring run, best first.
2. WHEN `mode=allocated` THEN THE SYSTEM SHALL return the candidates allocated to that job in the latest completed allocation round, at most `openings` of them.
3. THE SYSTEM SHALL show each candidate through the public profile view from spec 03 and SHALL include only candidates whose profile is `public` (proposed default; confirm with the team).
4. WHEN a non-member requests it THEN THE SYSTEM SHALL return 404.

### Requirement 3: Explanations

**User Story:** As a candidate or employer, I want to see why a match was made, so that I can trust or question it.

#### Acceptance Criteria
1. WHEN the candidate, or a member of the job's company, requests `GET /api/v1/matches/explanation?job_id=&candidate_id=` THEN THE SYSTEM SHALL return matched, related and missing skills and the graph paths behind related skills.
2. WHEN anyone else requests it, or no explanation exists, THEN THE SYSTEM SHALL return 404.

### Requirement 4: Extracted skills with evidence

**User Story:** As a candidate, I want to see which skills the platform read from my resume and why, so that I can correct mistakes.

#### Acceptance Criteria
1. WHEN a candidate requests `GET /api/v1/me/skills` THEN THE SYSTEM SHALL return the skills extracted from their primary resume and profile, each with its source text span and the backend that produced it (`baseline` or `agentic`).
2. THE SYSTEM SHALL include unlinked spans separately so the candidate can see what was not recognised.

### Requirement 5: Admin runs

**User Story:** As an admin, I want to start allocation rounds and fairness audits, so that I can run the batch pipeline on demand.

#### Acceptance Criteria
1. WHEN an admin posts `POST /api/v1/admin/allocation-rounds` THEN THE SYSTEM SHALL create a round with status `requested`, emit `allocation.requested` and return 202 with the round.
2. WHEN an admin posts `POST /api/v1/admin/audit-runs` with `backends` THEN THE SYSTEM SHALL create a run with status `requested`, emit `audit.requested` and return 202.
3. WHEN an admin requests either resource by id THEN THE SYSTEM SHALL return its current status and, when done, its results.
4. WHEN a non-admin calls these endpoints THEN THE SYSTEM SHALL return 403.
5. IF a round or run is already `requested` or `running` THEN THE SYSTEM SHALL return 409 with code `run_in_progress`.

### Requirement 6: Sync consent

**User Story:** As a candidate, I want to decide whether my careers profile may be shared with MyAcademic.

#### Acceptance Criteria
1. THE SYSTEM SHALL store `syncConsent` on the profile, default `false`, settable through `PUT` and `PATCH /api/v1/profiles/me`.
2. THE contract export from spec 03 SHALL NOT include `syncConsent`.

### Requirement 7: MyAcademic integration stub

**User Story:** As the MyAcademic developer, I want to read a consenting user's careers profile in the shared format, so that I can test sync before it is designed in full.

#### Acceptance Criteria
1. WHEN a request to `GET /api/v1/integrations/myacademic/profile?email=` carries header `X-Service-Token` equal to `MYACADEMIC_SERVICE_TOKEN` THEN THE SYSTEM SHALL return that user's contract export if `syncConsent` is true.
2. IF the token is missing or wrong THEN THE SYSTEM SHALL return 401; IF the user does not exist or has not consented THEN THE SYSTEM SHALL return 404.
3. THE SYSTEM SHALL compare the service token in constant time and SHALL log each call with the email and outcome, never the token.
4. THE SYSTEM SHALL NOT accept writes from MyAcademic until Gate C defines direction, scope and conflict handling.
