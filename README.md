# Multi-Currency Wallet Platform

A production-minded full-stack wallet platform supporting multi-currency wallets, deposits/withdrawals, currency conversion, peer-to-peer transfers, and transaction history.

## Features

- JWT authentication with bcrypt password hashing
- Multiple wallets per user (one per currency)
- Append-only transaction ledger
- Atomic transfers with row-level locking and idempotency
- Exchange rate integration (Frankfurter API) with scheduled refresh
- Cross-currency transfers and conversions with audit trail
- Paginated, filterable transaction history
- Structured JSON logging, health checks, Prometheus metrics
- Docker Compose local stack and GitHub Actions CI/CD

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis |
| Frontend | Next.js 15, TypeScript, React Query, TailwindCSS |
| Testing | Pytest, HTTPX, Testcontainers-ready |
| Infrastructure | Docker, Docker Compose, GitHub Actions |

## Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Health | http://localhost:8000/health |

## Local Development (without Docker for app)

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis 7

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start Postgres + Redis (or use docker compose up postgres redis)
export DATABASE_URL=postgresql+asyncpg://wallet:wallet@localhost:5432/wallet_db
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET_KEY=dev-secret

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

### Tests

```bash
cd backend
pytest tests/ -v --cov=app
```

## Deployment (Render)

1. Create managed PostgreSQL and Redis on Render
2. Deploy backend as Docker Web Service pointing to `backend/Dockerfile`
3. Set environment variables: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`
4. Run `alembic upgrade head` as release command
5. Deploy frontend as Web Service with `NEXT_PUBLIC_API_URL` pointing to API

## API Overview

Base path: `/api/v1`

| Endpoint | Description |
|---|---|
| `POST /auth/register` | Signup |
| `POST /auth/login` | Login (rate-limited) |
| `GET /auth/me` | Profile |
| `GET /wallets` | List wallets |
| `POST /wallets/{id}/deposit` | Deposit |
| `POST /wallets/{id}/withdraw` | Withdraw |
| `POST /conversions` | Convert between own wallets |
| `POST /transfers` | P2P transfer (supports `Idempotency-Key`) |
| `GET /transactions` | History with filters |
| `GET /health` | Health check |
| `GET /metrics` | Prometheus metrics |

## Assumptions

- Fiat currencies only (USD, EUR, GBP, JPY, CAD, AUD, CHF)
- Deposits/withdrawals are simulated (no payment gateway)
- Profile photo is URL-only (no file upload)
- Transfer recipient identified by email
- JWT access token only (15 min expiry)
- Single-region deployment for v1

## Trade-offs

| Decision | Rationale |
|---|---|
| Cached balance + ledger | Fast reads with full auditability |
| Synchronous transfers | Strong consistency over eventual consistency |
| Frankfurter API | Free, reliable ECB data; swappable via provider abstraction |
| Access-only JWT | Simpler v1; refresh tokens deferred |
| Integer minor units | Avoids floating-point financial errors |

## Known Limitations

- No refresh token rotation
- No file upload for profile photos
- Exchange rates depend on external provider availability
- Frontend stores JWT in localStorage (acceptable for demo; httpOnly cookie preferred in production)
- Scale features (partitioning, read replicas) documented but not implemented

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) — System design, data flow, scaling strategy
- [AI_USAGE.md](./AI_USAGE.md) — AI-assisted development transparency

## License

MIT
