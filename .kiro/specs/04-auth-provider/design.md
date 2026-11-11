# Design: auth provider (Clerk, decided 2026-10-27)

## What stays the same
- `Principal(user_id, email, role)` from spec 01. Views and permissions read only this.
- The `users` collection and its unique `(auth.provider, auth.subject)` index.
- Bearer tokens in the `Authorization` header. No cookies, so CSRF does not apply.

## Changes outside the Clerk class
- `users.role` may be `null` until the user picks one. `Principal.role` can be `None`.
- Permission classes from spec 01: when `request.user.role is None`, deny with code
  `role_required` instead of `forbidden`.
- `POST /api/v1/me/role` (`{"role": "candidate" | "employer"}`) uses a conditional update
  `update_one({"_id": id, "role": None}, {"$set": {"role": r}})`; zero matched gives 409 `role_already_set`.
- Management command `set_admin <email>`.
- `config/settings.py`: real class first; append `DevBearerAuthentication` only when
  `CAREERS_DEV_AUTH` is true.

## Clerk
Use a Clerk application created for careers only. MyAcademic keeps its own login and user records; nothing here reads or writes them (decision of 2026-10-03, Prof. Dhar and the MyAcademic team).

Flow: the React portal signs users in with Clerk's frontend SDK and sends Clerk's session
token as `Authorization: Bearer <jwt>`; the API verifies it locally (no call to Clerk per request).

`api/auth_clerk.py`:
```python
_jwks = PyJWKClient(settings.CLERK_JWKS_URL, cache_keys=True)   # refetches on unknown kid

class ClerkAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = bearer_token(request)              # None if absent or a "dev:" token
        if token is None: return None
        key = _jwks.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, key, algorithms=["RS256"], issuer=settings.CLERK_ISSUER,
                            leeway=5, options={"require": ["exp", "nbf", "sub", "iss"]})
        if "azp" in claims and claims["azp"] not in settings.CLERK_AUTHORIZED_PARTIES:
            raise AuthenticationFailed()           # Clerk: skip the check only when azp is absent
        if claims.get("sts") == "pending": raise AuthenticationFailed()
        user = users.get_or_create_external("clerk", claims["sub"], claims.get("email"), role=None)
        return (Principal(str(user["_id"]), user["email"], user["role"]), None)
```
Settings: `CLERK_ISSUER` (the instance's Frontend API URL), `CLERK_JWKS_URL`
(`<issuer>/.well-known/jwks.json`), `CLERK_AUTHORIZED_PARTIES` (comma list: the portal origins).
Clerk configuration: add a custom session-token claim `email` mapped to the user's primary
email. Checked 2026-10-27 against Clerk's manual JWT verification guide
(https://clerk.com/docs/guides/sessions/manual-jwt-verification): JWKS at the Frontend API URL
plus `/.well-known/jwks.json`, RS256, check `exp`/`nbf`, check `azp` when present, consider
rejecting `sts: pending`. The guide does not mention `iss`; checking it against `CLERK_ISSUER`
is an extra safeguard. For same-origin requests Clerk also sends a `__session` cookie; this API
ignores cookies and reads only the `Authorization` header, so CSRF protection is not needed.
Dependency: `PyJWT[crypto]`.

## Endpoint summary

| Endpoint | Auth |
|---|---|
| POST `/api/v1/me/role` | signed in with Clerk, role still null |

Sign-up, sign-in, sign-out and password reset are handled by Clerk's hosted components in the
portal; the API has no login endpoints.
