# Testing guide

## Local quality gate

Install development dependencies, then run:

```bash
ruff check .
pytest --cov --cov-report=term-missing --cov-fail-under=80
```

Verify schema creation and drift against a disposable database:

```bash
export DATABASE_URL=sqlite:////tmp/inkid-migration-test.db
alembic upgrade head
alembic check
```

Do not point destructive tests or migration experiments at a production database.

## Automated coverage

| Test module | Scope |
|---|---|
| `tests/test_api.py` | Dataset/writer lifecycle, pagination, audit API, admin flow, health, upload, prediction, and cleanup |
| `tests/test_uploads.py` | Invalid images and maximum upload size |
| `tests/test_storage.py` | S3 persistence/deletion behavior and locator guards |
| `tests/test_security.py` | API/admin authentication, production fail-closed, and same-origin enforcement |
| `tests/test_ml.py` | Cosine comparison and writer score aggregation |
| `tests/test_maintenance.py` | Audit retention and orphan cleanup |

The suite uses a temporary SQLite database, temporary upload directory, generated images, and a deterministic fake embedding. It deliberately avoids downloading model weights.

## Manual smoke test

Before a release, verify with synthetic images:

1. Unauthenticated API and admin calls are rejected in production mode.
2. Readiness fails with missing required security/storage configuration.
3. A dataset and at least two writers can be created.
4. Multiple valid reference images can be enrolled for each writer.
5. Invalid, oversized, and unsupported files are rejected without leftovers.
6. A query returns ranked candidates and honors threshold rejection.
7. Query images are deleted after success and failure.
8. Deleting a sample/writer/dataset removes its records and stored objects.
9. Audit events contain the expected actor, event, entity, and request ID.
10. The maintenance command removes only expired audit rows and eligible orphans.

## Tests requiring a real environment

These cannot be proven by the SQLite/unit suite and are mandatory before a real production launch:

- PostgreSQL migration, concurrency, failover, backup, and restore testing;
- S3 IAM, encryption, lifecycle, deletion, outage, and throttling testing;
- full CPU model load/inference using pinned container dependencies;
- container image build, vulnerability scan, non-root execution, and health check;
- ingress TLS, body limits, authentication, rate limits, and security headers;
- load/soak testing with representative dataset sizes and concurrency;
- held-out ML evaluation described in the model card;
- disaster recovery and application rollback rehearsal.

Record commands, versions, timestamps, environment, results, and approver for each external test. “It worked once” is not a reproducible acceptance result.
