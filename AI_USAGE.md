# AI Usage Disclosure

## Tools Used

- **Cursor IDE** with Claude-based AI agent for architecture design, code generation, and documentation
- AI-assisted file creation across backend, frontend, tests, Docker, and CI configuration

## How AI Accelerated Development

| Area | AI Contribution |
|---|---|
| Architecture | Phase 1 system design, ERD, API contract, trade-off analysis |
| Backend scaffold | Clean architecture folder structure, domain models, repositories, services |
| Transfer logic | Concurrency control patterns (`FOR UPDATE`, idempotency, lock ordering) |
| Frontend | Next.js pages, React Query hooks, Tailwind UI components |
| Testing | Unit and integration test scaffolding |
| DevOps | Docker Compose, GitHub Actions workflow, deployment docs |
| Documentation | README, ARCHITECTURE.md, observability strategy |

## AI Suggestions Accepted

- **Integer minor units** for money storage (avoid float errors)
- **Cached balance + append-only ledger** (fast reads, full audit trail)
- **Frankfurter API** as free exchange provider with abstraction layer
- **Deterministic wallet lock ordering** to prevent deadlocks
- **Idempotency keys** on transfers via unique DB constraint
- **FakeRedis in tests** for rate limiting without external Redis dependency
- **Prometheus metrics** endpoint for observability readiness
- **APScheduler** for in-process rate refresh (simple for v1)

## AI Suggestions Rejected

- **SQLite for tests** — Rejected in favor of PostgreSQL for fidelity on locking/constraints
- **Refresh token rotation in v1** — Rejected to reduce scope; documented as limitation
- **Celery for async transfers** — Rejected; synchronous DB transactions required for consistency
- **Pure derived balances** — Rejected; cached balance chosen for read performance
- **httpOnly cookie auth in v1** — Partially rejected; localStorage used for demo simplicity (documented trade-off)
- **Full CQRS implementation** — Rejected for v1; documented in scale exercise only

## Human Engineering Decisions

- **Clean Architecture layer boundaries** — Human-defined structure per assignment requirements
- **Transfer consistency as top priority** — Explicit design choice for financial correctness
- **Append-only ledger invariant** — Non-negotiable domain rule enforced at all layers
- **Evaluation rubric alignment** — Architecture weighted 25%; effort prioritized accordingly
- **Scope control** — MVP per phase rather than feature maximization
- **Security baseline** — bcrypt, JWT, rate limiting, input validation regardless of AI suggestions
- **Documentation completeness** — README assumptions, trade-offs, and scale exercise required for review

## Verification

All AI-generated code was reviewed for:
- Correctness of transfer atomicity and locking
- Domain invariant enforcement
- API contract alignment between frontend types and backend schemas
- Test coverage of critical paths (wallet, transfer, auth flows)
