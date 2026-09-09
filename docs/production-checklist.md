# Production acceptance checklist

This checklist distinguishes application completeness from deployment approval. Mark an item complete only when evidence is linked or recorded; do not convert unknowns into assumed passes.

## Ownership and policy

- [ ] A named service owner, technical owner, security contact, and incident contact exist.
- [ ] The intended use and explicitly prohibited uses are approved.
- [ ] Privacy/legal review determines how handwriting images and embeddings are classified.
- [ ] Notice/consent or other lawful basis is documented for the intended population.
- [ ] Retention, access, subject-request, deletion, and breach procedures are approved.
- [ ] A human-review and appeal path exists for every consequential outcome.

## Model acceptance

- [ ] A versioned, consented, representative dataset manifest exists.
- [ ] Writer-disjoint development, calibration, and test partitions are frozen.
- [ ] The threshold is selected on calibration data only.
- [ ] Held-out top-1, FAR, FRR, rejection rate, confidence intervals, and subgroup/capture-condition results are approved.
- [ ] Unknown-writer, poor-quality, spoof/tracing, and distribution-shift tests are documented.
- [ ] The deployed model identifier, weights, preprocessing, and threshold match the evaluation artifact.
- [ ] Monitoring and rollback criteria for model-quality drift are defined.

## Infrastructure

- [ ] An immutable, scanned container image is stored by digest.
- [ ] PostgreSQL is private, encrypted, least-privilege, monitored, and backed up with point-in-time recovery.
- [ ] The private S3 bucket has block-public-access, least-privilege policy, encryption, lifecycle, and access logging.
- [ ] TLS and ingress upload limits are enforced.
- [ ] Secrets are held in a secret manager/workload identity and rotation has been tested.
- [ ] Production and non-production accounts/data are separated.
- [ ] Capacity, load, soak, and dependency-failure tests meet approved objectives.

## Release and operations

- [ ] Migration and backward-compatible rollback plans are reviewed.
- [ ] `/health/live` and `/health/ready` are monitored from outside the instance.
- [ ] Synthetic enrolment, prediction, deletion, and S3 checks run without personal data.
- [ ] Logs and audit events are centralized with access and retention controls.
- [ ] Alerts cover availability, latency, errors, resources, database, storage, authentication, and backups.
- [ ] Audit retention and orphan maintenance are scheduled.
- [ ] Backup restoration has been exercised and recovery time/point recorded.
- [ ] Application rollback and incident-response exercises have been completed.
- [ ] A decommissioning and data-erasure plan exists.

## Release record

Complete this table for each production release:

| Field | Evidence |
|---|---|
| Release owner | |
| Approval date | |
| Git commit | |
| Container digest | |
| Alembic revision | |
| Model identifier | |
| Threshold | |
| Evaluation report | |
| Load-test report | |
| Security review | |
| Backup/restore test | |
| Rollback version | |
| Open risks and owners | |

Production approval requires explicit sign-off by the responsible owners. Production-safety claims unsupported by evidence should block release.
