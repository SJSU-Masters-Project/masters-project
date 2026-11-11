---
inclusion: always
---

# Product: Careers backend (careers.myacademic.org)

## What this is
The backend API for the careers platform of the CMPE 295A/B master's project
"Beyond Keyword Matching: An Agentic, Auditable System for Candidate-Job Matching and Hiring"
(SJSU, advisor Dr. Subhankar Dhar). The backend API is owned by Himanshu Jain.

It is a separate microservice from the main MyAcademic website, with its own users,
its own auth and its own MongoDB data. It is the gateway that the React portal talks to.
Other project services (skill extraction, knowledge graph and GNN scorer, allocation,
explanations, fairness audit, screening interviewer) sit behind it and share MongoDB.

## Users and roles
- candidate: builds a profile, uploads resumes, browses jobs, sees matches later.
- employer: belongs to a company, posts jobs, marks each skill required or optional,
  states the number of openings, reviews matched candidates later.
- admin: runs allocation rounds and fairness audits, manages users.

## Scope for CMPE 295A (prototype due 2026-12-04)
Agreed with the advisor on 2026-09-30: auth flows, resume upload and job posting.
The 2026-12-04 demo also needs profiles and jobs stored, the other components
reachable through this API, and an integration stub for the advisor's platform.

## Rules that come from the advisor and team decisions
- Careers keeps its own auth and user records, separate from MyAcademic (agreed 2026-10-03).
- Profile sync with MyAcademic is opt-in and user-controlled, never tied to sign-in (2026-10-03).
- The shared profile schema v1.0 (backend/contracts/) is the contract for that sync.
- Public profiles are visible to all logged-in users, like LinkedIn (2026-09-30).
- Agents and services add evidence; they never reject a candidate (requirement N4).
- The university does not pay for hosting: keep resource use small (t3.micro, Atlas free tier).

## Not decided yet (do not build without a decision)
- Auth provider (Clerk vs self-managed) and the exact auth/backend boundary with Eshan.
- Sync direction, scope, conflict handling and account linking with MyAcademic.
- Collection contracts with the other services' owners.
