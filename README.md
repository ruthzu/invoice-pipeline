# Invoice Pipeline

Invoice Pipeline is a FastAPI service that accepts invoice documents, queues them
for background processing, extracts structured data with Gemini, and routes each
invoice for automatic approval or human review.

## Architecture

An upload creates an invoice record and enqueues a job in Redis-backed RQ. The
worker reads the stored document and sends it to the extraction provider. The
result then passes through confidence heuristics and validation before routing
decides whether it is auto-approved or needs review. Reviewers can approve or
reject invoices through the API.

## Setup

From a clean clone:

```bash
git clone https://github.com/ruthzu/invoice-pipeline.git
cd invoice-pipeline
cp .env.example .env
# Edit .env and set GEMINI_API_KEY, plus non-default database credentials.
docker compose up -d --build
docker compose exec api alembic upgrade head
python scripts/seed_demo.py
```

The API is available at `http://localhost:8000`; PostgreSQL is exposed locally
on port `5433` by the development override file.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Report database, Redis, and queue health. |
| GET | `/metrics` | Return invoice status counts and extraction aggregates. |
| GET | `/invoices` | List invoices, optionally filtered by status. |
| POST | `/invoices` | Upload a PDF, JPEG, or PNG invoice. |
| POST | `/invoices/{invoice_id}/approve` | Approve an invoice needing review. |
| POST | `/invoices/{invoice_id}/reject` | Reject an invoice with a reason. |

## Known Limitations

Enqueue failures are logged but do not have automatic recovery. Reviewer identity
is currently a hardcoded placeholder because there is no real authentication or
user system. The health and metrics endpoints are unauthenticated and should be
gated before public exposure. There is also no CI/CD pipeline yet; tests and lint
are run locally.

<!-- ## What I'd do next

I would add CI/CD with automated tests and linting, introduce real authentication
and reviewer accounts, and use an outbox or reconciliation pattern to make
queueing reliable. -->
