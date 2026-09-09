# Deployment guide

## Supported profiles

| Profile | Database | Object storage | Intended use |
|---|---|---|---|
| Local Python | SQLite | Local directory | Development |
| Docker Compose default | SQLite in `/data` | `/data/uploads` volume | Single-host demonstration |
| Production | PostgreSQL | Private S3 bucket | Shared, durable deployment |

SQLite/local storage must not be used with multiple replicas.

## Required production configuration

```dotenv
APP_ENV=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
STORAGE_BACKEND=s3
S3_BUCKET=private-inkid-bucket
S3_PREFIX=handwriting-samples
API_KEY=<random high-entropy secret>
ADMIN_USERNAME=<non-default operator name>
ADMIN_PASSWORD=<random high-entropy secret>
MAX_UPLOAD_BYTES=10485760
MAX_IMAGE_PIXELS=40000000
```

For Compose, provide the PostgreSQL URL as `COMPOSE_DATABASE_URL`. AWS access uses the standard boto3 credential chain. Prefer workload identity or an instance/service role; if static credentials are unavoidable, inject them through the platform secret manager. Never bake secrets into an image or commit them to Git.

## PostgreSQL preparation

1. Create an application database and a least-privilege application role.
2. Require encrypted connections according to the provider configuration.
3. Configure automated backups and point-in-time recovery.
4. Set connection/session limits appropriate to the number of application workers.
5. Run `alembic upgrade head` using a controlled release job.
6. Run `alembic check` against the deployed revision during release verification.

The current application does not ship a connection pooler. Add a provider pooler such as PgBouncer when the deployment model or connection budget requires it.

## S3 preparation

The bucket must be private. The application identity requires only:

- `s3:PutObject` for the configured prefix;
- `s3:DeleteObject` for the configured prefix;
- encryption permissions if a customer-managed key is selected.

Public read access and bucket listing are not required. Enable block-public-access, versioning where policy permits, server access/audit logging, and lifecycle rules aligned with the approved retention policy. The application requests AES-256 server-side encryption on upload; production owners may enforce stronger bucket-side encryption policies.

## Container release

Build an immutable image tagged with the Git commit:

```bash
docker build -t registry.example/inkid:<git-sha> .
docker push registry.example/inkid:<git-sha>
```

The supplied image:

- uses Python 3.12 slim;
- installs CPU PyTorch from the official CPU wheel index;
- runs as a non-root user;
- listens on port `8000`;
- runs migrations before Uvicorn in its default command;
- exposes `/health/ready` as its container health check.

For a multi-replica platform, override the default command: run migrations as a single release job, then start replicas with `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Do not let every replica race the same migration.

## Network controls

- Terminate TLS at a trusted ingress or load balancer.
- Restrict PostgreSQL to private network access from the application.
- Restrict S3 access to the application identity and approved administrative identities.
- Do not expose the operator console without authentication and TLS.
- Apply request/body limits at the ingress at least as strict as `MAX_UPLOAD_BYTES`.
- Restrict `/docs` in production if public API discovery is not intended.

## Release sequence

1. Confirm backup freshness and rollback image availability.
2. Build, scan, and sign the image according to organizational policy.
3. Apply migrations once.
4. Deploy one canary instance with production configuration.
5. Verify `/health/live`, `/health/ready`, authentication rejection, CRUD, sample enrolment, prediction, deletion, audit creation, and object cleanup.
6. Expand traffic gradually while watching error rate, latency, memory, CPU, database connections, and object-storage errors.
7. Record the deployed image digest, migration revision, configuration version, and acceptance evidence.

## Rollback

Application rollback is safe only when the previous version can read the current database schema. Alembic downgrade is not an automatic incident response: take a verified backup first and review whether the migration is data-destructive. Prefer rolling the application image back while leaving backward-compatible schema additions in place.
