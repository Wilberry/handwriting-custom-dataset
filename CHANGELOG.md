# Changelog

This project follows a simple release-oriented changelog. Versions are assigned when a release is tagged.

## Unreleased

### Added

- Full dataset, writer, and sample create/read/update/delete lifecycle
- Validated bounded image uploads and safe temporary-file cleanup
- Versioned ResNet-50 embeddings, writer-level score aggregation, and top-three predictions
- Leave-one-out evaluation command with threshold, accuracy, FAR, and FRR output
- API-key and operator authentication, same-origin form validation, and security headers
- Structured request logging, request IDs, audit events, and retention/orphan maintenance
- Alembic migrations, PostgreSQL support, local/S3 storage abstraction, Docker, Compose, and health endpoints
- Responsive operator console, automated tests, coverage gate, and comprehensive project documentation

### Changed

- Clarified the product as writer identification rather than OCR or custom model training
- Removed storage locators and raw embedding data from API responses
- Added pagination and explicit prediction response contracts

### Removed

- Empty, unused `app/ml_engine.py` placeholder
