# InkID — Custom-Dataset Handwriting Identification

A FastAPI portfolio project for enrolling handwriting samples and identifying the closest enrolled writer. It includes a REST API and a responsive, server-rendered operator console.

> InkID performs **writer identification**, not handwritten-text transcription (OCR). Uploaded samples form a reference collection; they do not fine-tune or retrain ResNet-50.

## Project status

The repository implements a complete portfolio-grade writer-identification workflow. It is not automatically approved for use with real personal data: production deployment requires representative model evidence, approved data governance, provisioned infrastructure, and recorded acceptance checks.

| Area | Repository status | Production dependency |
|---|---|---|
| Application workflow | Implemented and locally tested | Synthetic end-to-end deployment check |
| Database and storage | SQLite/local plus PostgreSQL/S3 adapters | Managed services, credentials, backup/restore evidence |
| Security and operations | Baseline controls and runbooks implemented | TLS, secret manager, monitoring, rate limits, incident ownership |
| ML evaluation | Leave-one-out tool implemented | Representative writer-disjoint data and approved threshold |
| Privacy | Data minimization/deletion controls documented | Consent/lawful basis, retention, access, and deletion policy |

## Implemented

- Dataset, writer, and sample CRUD with database constraints and Alembic migrations
- Validated JPEG, PNG, and WebP uploads with byte, pixel, and filename safeguards
- 2,048-dimensional embeddings from pretrained Torchvision ResNet-50
- Cosine comparison, strongest-sample aggregation per writer, top-three candidates, and configurable acceptance threshold
- Local filesystem or private S3 reference-image storage
- SQLite development and PostgreSQL production support through SQLAlchemy
- API-key protection, HTTP Basic operator access, same-origin form checks, security headers, and production configuration checks
- Request IDs, structured request logs, protected audit events, retention cleanup, and orphan-file cleanup
- Paginated collection endpoints that do not expose object locators or embedding bytes
- Responsive operator UI, liveness/readiness endpoints, CPU container, Compose configuration, tests, linting, and CI
- Leave-one-out evaluation CLI reporting top-1 accuracy, a derived threshold, false-accept rate, and false-reject rate

## Architecture

```mermaid
flowchart TD
    U["Validated reference"] --> E["ResNet-50 embedding"]
    E --> D["SQL metadata + vector"]
    U --> O["Local or S3 storage"]
    Q["Validated query"] --> C["Cosine similarity"]
    D --> C
    C --> W["Top-k writer aggregation"]
```

The first ML operation downloads standard Torchvision ResNet-50 weights when they are not cached. Every response includes an `X-Request-ID`, MIME-sniffing and frame protections, and a strict referrer policy. Operator pages also receive a Content Security Policy. Request logs omit query strings and credentials.

## Documentation

- [Documentation index](docs/README.md)
- [Architecture](docs/architecture.md)
- [API guide](docs/api.md)
- [Deployment guide](docs/deployment.md)
- [Operations runbook](docs/operations.md)
- [Security and privacy](docs/security-privacy.md)
- [Model card and evaluation protocol](docs/model-card.md)
- [Testing guide](docs/testing.md)
- [Production acceptance checklist](docs/production-checklist.md)
- [Contributing](CONTRIBUTING.md) and [changelog](CHANGELOG.md)

## Local setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Open the operator console at `http://127.0.0.1:8000/admin`, API documentation at `http://127.0.0.1:8000/docs`, or the API root at `http://127.0.0.1:8000/`.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST`, `GET` | `/datasets/` | Create or list datasets |
| `PUT`, `DELETE` | `/datasets/{dataset_id}` | Rename or delete a dataset |
| `POST` | `/students/` | Enrol a writer |
| `GET` | `/students/{dataset_id}` | List a dataset's writers |
| `PUT`, `DELETE` | `/students/{student_id}` | Rename or delete a writer |
| `POST` | `/samples/{student_id}` | Upload a reference sample |
| `GET` | `/samples/` | List sample metadata |
| `DELETE` | `/samples/{sample_id}` | Delete a sample and its object |
| `POST` | `/predict/` | Identify a query's nearest writer candidates |
| `GET` | `/audit-events/` | List newest audit events |
| `DELETE` | `/audit-events/retention` | Purge audit events older than a window |
| `GET` | `/health/live`, `/health/ready` | Process and dependency health |

Collection endpoints accept `offset` (default `0`) and `limit` (default `50`, maximum `200`). Protected REST calls use `X-API-Key`. Stored object locators and embeddings are never returned.

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `DATABASE_URL` | `sqlite:///./app.db` | SQLAlchemy database URL |
| `UPLOAD_DIR` | `uploads` | Local reference-image directory |
| `MAX_UPLOAD_BYTES` | `10485760` | Maximum upload size in bytes |
| `MAX_IMAGE_PIXELS` | `40000000` | Maximum decoded image area |
| `STORAGE_BACKEND` | `local` | `local` or `s3` reference storage |
| `S3_BUCKET` | unset | Private bucket required by the S3 backend |
| `S3_PREFIX` | `handwriting-samples` | S3 object-key prefix |
| `APP_ENV` | `development` | Runtime environment |
| `API_KEY` | unset | REST credential supplied as `X-API-Key` |
| `ADMIN_USERNAME` | unset | Operator-console HTTP Basic username |
| `ADMIN_PASSWORD` | unset | Operator-console HTTP Basic password |

Copy `.env.example` to `.env`. Authentication may be omitted in development. With `APP_ENV=production`, protected requests fail closed unless all credentials are configured. Use `postgresql+psycopg://user:password@host/database` for PostgreSQL. S3 uses the standard AWS SDK credential chain; never commit access keys.

## Migrations and containers

Apply migrations before every release:

```bash
alembic upgrade head
```

The container installs CPU-only PyTorch, runs as a non-root user, applies migrations before startup, exposes a readiness health check, and defaults to a persistent `/data` volume:

```bash
docker compose up --build
```

Set `COMPOSE_DATABASE_URL`, `STORAGE_BACKEND=s3`, `S3_BUCKET`, and AWS credentials to use PostgreSQL and S3 with Compose. Outside Compose, use `DATABASE_URL` directly. Multiple application instances require shared PostgreSQL and object storage.

## Evaluation and maintenance

After enrolling at least two samples per writer, evaluate the stored dataset:

```bash
python -m app.evaluation --dataset-id 1
```

The results describe the enrolled dataset only; a separate held-out dataset is required for a defensible generalization claim.

Audit events store the actor, event type, entity, request ID, timestamp, and JSON details—not images or embeddings. Apply retention and remove old unreferenced local files with:

```bash
python -m app.maintenance --audit-retention-days 365 --orphan-grace-hours 24
```

Schedule maintenance externally. Database backups, S3 lifecycle rules, encryption-key ownership, and restore exercises are deployment responsibilities.

## Development checks

```bash
pip install -r requirements-dev.txt
ruff check .
pytest --cov --cov-report=term-missing --cov-fail-under=80
alembic upgrade head
alembic check
```

GitHub Actions runs these checks for pull requests and pushes to `main`.

## Remaining production release gates

The repository is complete as a portfolio-grade writer-ID service. A real-data launch remains blocked until these external evidence and infrastructure tasks are completed:

1. Approve consent, retention, deletion, and access policies for the intended users.
2. Measure held-out accuracy, false-accept, and false-reject rates for the target population.
3. Calibrate the threshold and document a human-review/fallback process.
4. Provision managed PostgreSQL/S3, backups, restore testing, monitoring, TLS, and secret rotation.
5. Perform load and failure testing against expected inference traffic.

ResNet-50 is a generic visual feature extractor, not a handwriting-specialized verification model. Authentication provides API and operator boundaries, not multi-tenant role-based identity. CPU inference is synchronous and suited to modest traffic; high-volume use needs a bounded queue and dedicated model serving. InkID must not be treated as OCR, authorship proof, or a basis for grading, discipline, biometric, or other high-stakes decisions.

## License

MIT
