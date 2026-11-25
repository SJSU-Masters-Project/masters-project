# Implementation Plan

**Decision recorded (2026-10-27): Clerk.** The self-managed tasks are removed. Confirmed by
Eshan. Portal-side ownership and the role-selection screen are a frontend concern (see the
note in requirements.md); the API side below is implemented.

- [x] 1. Record the decision
  - Clerk, confirmed by Eshan on 2026-10-27 (top of requirements.md).
  - _Requirements: 1.1_

- [x] 2. Nullable role and role selection
  - Allow `role: null` in users; update permission classes to deny with `role_required`.
  - `POST /api/v1/me/role` with the conditional update; `set_admin` management command.
  - Tests: null-role user gets 403 `role_required` on a candidate endpoint; role set once; second attempt 409; `set_admin` grants admin; candidate cannot self-assign admin (400).
  - _Requirements: 2.2, 2.3, 2.4, 2.5_

- [x] 3. Settings switch and production guard
  - Put the real class first; add dev auth only when `CAREERS_DEV_AUTH` is true.
  - Tests: with `CAREERS_DEV_AUTH` false a `Bearer dev:...` header gets 401; the spec 01 system check still fires on the bad combination.
  - _Requirements: 1.1, 1.2, 3.1, 3.2_

- [x] 4. Clerk token verification
  - `api/auth_clerk.py` per design.md; settings and `.env.example` entries; spectacular extension; add `PyJWT[crypto]`.
  - Tests with a locally generated RSA key pair and a patched `PyJWKClient`: valid token 200; token without `azp` 200; expired, future `nbf`, wrong issuer, wrong `azp`, `sts: pending`, wrong signature, `alg: none` and HS256-signed tokens all 401; first call creates the user with role null; second call reuses it; no outbound call is made during sign-in.
  - _Requirements: 1.2, 1.3, 2.1, 3a.1, 3a.2, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5. Clerk setup handover
  - Documented in README the Clerk dashboard steps: add the custom `email` claim to the session token, list the portal origins as authorized parties, and the three settings. The Clerk application is careers-only, separate from MyAcademic. Claim names confirmed against Clerk's docs (https://clerk.com/docs/guides/sessions/manual-jwt-verification).
  - _Requirements: 4.4_

- [x] 6. Docs and frontend handover
  - README "Authentication" section; `spectacular --validate --fail-on-warn` passes; frontend sign-in flow documented: call Clerk's `getToken()` before each API request and send it as `Authorization: Bearer <token>` (session tokens are short-lived, so never cache one).
  - _Requirements: 1.3_
