# Contributing

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Use synthetic images and identities in development. Never commit `.env`, databases, model caches, personal handwriting, generated coverage files, or cloud credentials.

## Change workflow

1. Create a focused branch from `main`.
2. Keep application behavior, migrations, tests, and documentation in the same pull request.
3. Add an Alembic revision for every schema change; do not edit an already-deployed revision.
4. Preserve backward compatibility for rolling releases or document the required maintenance window.
5. Run the local quality gate before requesting review.

```bash
ruff check .
pytest --cov --cov-report=term-missing --cov-fail-under=80
alembic check
```

## Review expectations

Pull requests should explain purpose, user-visible behavior, security/privacy impact, migration/rollback implications, and verification. Changes to model weights, preprocessing, aggregation, or thresholds require a new model identifier and evaluation evidence described in the [model card](docs/model-card.md).

Changes affecting uploads, authorization, deletion, storage locators, audit records, or personal data require an explicit security/privacy review. Do not weaken limits or expose internal fields merely to simplify a client.

## Style

- Keep endpoint contracts explicit with Pydantic response models.
- Keep storage and ML dependencies lazy where startup does not require them.
- Centralize database operations and translate domain failures into stable HTTP errors.
- Prefer deterministic unit tests; isolate network, cloud, and model downloads from the default suite.
- Update the relevant document when operational behavior changes.

## Reporting security issues

Do not open a public issue containing credentials, personal data, exploit details, or vulnerable deployment information. Contact the repository owner privately and include affected versions, reproduction conditions, impact, and suggested containment when known.
