# Requirements Document

> **Decision (2026-10-27): Clerk.** Confirmed by Eshan; the self-managed option is removed.
> Still to confirm before task 2: who builds the portal side (Clerk's React components) and
> whether role selection after first sign-in (Requirement 2) is what the portal will show.
> The API side of this spec is Himanshu's.

## Introduction

Replace development authentication with real sign-in for careers, which has its own users,
separate from MyAcademic (agreed 2026-10-03). The API keeps the `Principal` interface from
spec 01, so specs 02 and 03 do not change. Dev auth stays for local runs and tests only.
Eshan raised Clerk on 2026-09-30 and confirmed it on 2026-10-27.

## Requirements

### Requirement 1: Real authentication on every protected endpoint

**User Story:** As a user, I want my account protected by real sign-in, so that nobody can act as me.

#### Acceptance Criteria
1. THE SYSTEM SHALL list the real authentication class first in `DEFAULT_AUTHENTICATION_CLASSES` and keep `DevBearerAuthentication` only when `CAREERS_DEV_AUTH` is true.
2. WHEN a request has no valid credentials THEN protected endpoints SHALL return 401 with code `not_authenticated` or `authentication_failed`.
3. THE SYSTEM SHALL register a drf-spectacular authentication extension for the new class.

### Requirement 2: Choosing a role

**User Story:** As a new user, I want to say whether I am a candidate or an employer, so that I see the right features.

#### Acceptance Criteria
1. WHEN a user signs in through the external provider for the first time THEN THE SYSTEM SHALL create their `users` record with `role` null.
2. WHEN a user with a null role posts `POST /api/v1/me/role` with `candidate` or `employer` THEN THE SYSTEM SHALL set it once and return the user.
3. IF the role is already set THEN THE SYSTEM SHALL return 409 with code `role_already_set`.
4. WHEN a user with a null role calls an endpoint that needs a role THEN THE SYSTEM SHALL return 403 with code `role_required`.
5. THE SYSTEM SHALL let only the management command `python manage.py set_admin <email>` grant the `admin` role.

### Requirement 3: Remove development shortcuts from production

**User Story:** As the person deploying, I want to be sure no test login works in production.

#### Acceptance Criteria
1. WHEN the production settings are loaded THEN `CAREERS_DEV_AUTH` SHALL be false and the startup check from spec 01 SHALL pass.
2. THE production smoke test SHALL confirm that a `Bearer dev:...` header returns 401.

### Requirement 3a: Careers sign-in stays separate from MyAcademic

**User Story:** As a careers user, I want my careers account to be its own, so that I can use careers without a MyAcademic account (agreed 2026-10-03).

#### Acceptance Criteria
1. THE SYSTEM SHALL trust only tokens from a Clerk application created for careers alone; it SHALL NOT share a Clerk instance, user pool or session with the main MyAcademic site.
2. WHEN a user signs in or signs up THEN THE SYSTEM SHALL NOT call MyAcademic or look the user up there; profile sync is a separate, user-controlled action (spec 05, Requirements 6 and 7).

### Requirement 4: Verify Clerk session tokens

**User Story:** As the backend, I want to trust only tokens that Clerk signed for this app.

#### Acceptance Criteria
1. WHEN a request carries `Authorization: Bearer <token>` THEN THE SYSTEM SHALL verify its RS256 signature against Clerk's JWKS, cached and refreshed when a new key id appears.
2. THE SYSTEM SHALL reject tokens that are expired, not yet valid (allowing 5 seconds of clock skew), from a different issuer than `CLERK_ISSUER`, or that carry an `azp` claim not in `CLERK_AUTHORIZED_PARTIES` (Clerk's guide: skip the `azp` check only when the claim is absent).
5. IF a token carries `sts` equal to `pending` THEN THE SYSTEM SHALL reject it with 401 (Clerk sets this only when Organizations are used without personal accounts; the project does not use Organizations, so this is a safeguard).
3. WHEN a valid token arrives THEN THE SYSTEM SHALL find or create the user with `auth.provider` `clerk` and `auth.subject` equal to the token's `sub`.
4. THE SYSTEM SHALL take the user's email from a custom session-token claim `email` configured in the Clerk dashboard.
