# Design: service integration (GATED)

## Pattern
```
API writes jobs/profiles/resumes ──► events (outbox)
                                        │  each service polls with its own checkpoint
                                        ▼
                    skill extraction · graph + scorer · allocation · explanations · audit
                                        │  each writes ONLY its own collections
                                        ▼
API reads those collections ──► portal
```
Rules for every service collection:
- One owner writes it; the API only reads (except `requested` run documents, below).
- Every document has `created_at`; result sets carry a `run_id` so the API can pick the
  latest completed run.
- Ids that point at careers data are ObjectIds of `users`, `jobs` or `resumes`.

## Proposed collection shapes (agree each with its owner: Gate B)

### extracted_skills (owner: Uday)
```json
{ "_id": ObjectId, "entity_type": "resume", "entity_id": ObjectId, "user_id": ObjectId,
  "backend": "baseline", "run_id": "extract-2026-11-05",
  "skills": [ {"label": "Python", "esco_uri": "http://data.europa.eu/esco/skill/...",
               "span": "built ETL jobs in Python", "score": 0.82,
               "source": "linked"} ],
  "unlinked_spans": [ {"span": "Spine", "best_label": "spine surgery", "best_score": 0.53} ],
  "created_at": ISODate }
```
`source`: `linked` (baseline linker), `resolved` (agent mapped an unlinked term) or `inferred`
(agent inferred an unstated skill; must quote its evidence span).
Index: `[("entity_type",1), ("entity_id",1), ("backend",1), ("created_at",-1)]`.

### score_runs and match_scores (owner: Himanshu, scorer)
```json
score_runs:   { "_id": "gnn-2026-11-12", "model": "gnn", "status": "done",
                "created_at": ISODate, "finished_at": ISODate }
match_scores: { "run_id": "gnn-2026-11-12", "job_id": ObjectId, "candidate_user_id": ObjectId,
                "score": 0.71, "rank_for_job": 3, "rank_for_candidate": 1,
                "confidence_band": "high", "created_at": ISODate }
```
`confidence_band` follows the LinkedIn-style high / medium / low indicator adopted in the
project framing. The thresholds belong to the scorer, not the API.
Indexes: `[("run_id",1), ("job_id",1), ("rank_for_job",1)]`,
`[("run_id",1), ("candidate_user_id",1), ("rank_for_candidate",1)]`.

### allocation_rounds and allocations (owner: Eshan, allocation engine)
```json
allocation_rounds: { "_id": ObjectId, "status": "requested", "method": "deferred_acceptance",
                     "score_run_id": "gnn-2026-11-12", "requested_by": ObjectId,
                     "created_at": ISODate, "started_at": null, "finished_at": null, "error": null }
allocations:       { "round_id": ObjectId, "job_id": ObjectId, "candidate_user_id": ObjectId,
                     "created_at": ISODate }
```
The API inserts the round with `status: requested`; the engine moves it to `running`, then
`done` or `failed`, and writes `allocations`. The number of allocations per job must not
exceed the job's `openings`.

### explanations (owner: Himanshu)
```json
{ "run_id": "gnn-2026-11-12", "job_id": ObjectId, "candidate_user_id": ObjectId,
  "matched_skills": ["Python"], "missing_skills": ["Kubernetes"],
  "related_skills": [ {"candidate_skill": "Docker", "job_skill": "Kubernetes",
                       "path": ["Docker", "container orchestration", "Kubernetes"]} ],
  "created_at": ISODate }
```

### audit_runs (owner: Uday)
Same lifecycle as allocation rounds, plus `backends: ["baseline", "agentic"]` and a `results`
object the audit writes (impact ratios per group and backend). The API returns `results` as is.

## API behaviour
- "Latest completed run": `score_runs.find({"status": "done"}).sort("finished_at", -1).limit(1)`.
- `GET /me/matches`: join `match_scores` (candidate, latest run) to `jobs` with `status: open`;
  page with spec 01 pagination.
- `GET /jobs/{id}/matches`: membership check from spec 02; `ranked` reads `match_scores`;
  `allocated` reads `allocations` of the latest `done` round; candidates without a public
  profile are left out (Requirement 2.3 default).
- Admin runs: one `requested` or `running` document at a time per kind, checked with
  `find_one({"status": {"$in": ["requested", "running"]}})` before inserting. Two admins
  clicking within milliseconds could both insert; that is acceptable for a manual admin action
  in the prototype. A database-enforced lock would need the engine to release it, so it waits
  for the owners' agreement.
- Event types added: `allocation.requested`, `audit.requested`.

## MyAcademic stub (Part B)
- `syncConsent` is stored next to `visibility` on the profile; never exported.
- `ServiceTokenAuthentication`: reads `X-Service-Token`, compares with
  `hmac.compare_digest(token, settings.MYACADEMIC_SERVICE_TOKEN)`, returns
  `Principal(user_id="service:myacademic", email="", role="service")`. Used only on
  `/api/v1/integrations/...` views; a `IsService` permission allows only it.
- Lookup by email because account linking (Gate C) is not designed. Replace with the agreed
  link once it is.
- Logging: `logger.info("myacademic_export", extra={"email": email, "outcome": "ok|no_consent|not_found"})`.
- No write endpoints until Gate C.

## Testing approach
Tests seed the service collections directly with documents in the agreed shapes. This also
makes the agreed shapes executable: if an owner changes a shape, the seed fixtures and these
tests change in the same pull request.
