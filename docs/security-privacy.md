# Security and privacy

## Data classification

Handwriting reference images and embeddings may be personal data and may be treated as biometric or otherwise sensitive data depending on purpose and jurisdiction. Writer names are identifiers. Query images can contain unintended text or personal information even though the system does not perform OCR.

The deployment owner must obtain legal/privacy review for the intended population and use. This document is engineering guidance, not a legal determination.

## Implemented controls

| Area | Control |
|---|---|
| Authentication | Constant-time API-key and HTTP Basic comparisons; production fails closed when credentials are missing |
| Browser forms | Same-origin validation for state-changing operator actions |
| Uploads | Streamed byte limit, allowed decoded formats, pixel limit, UUID filenames, temporary-query cleanup |
| Data exposure | API schemas omit storage locators and embeddings |
| Storage | Private backend design; S3 upload requests server-side AES-256 encryption |
| Database | Parameterized ORM operations, uniqueness constraints, foreign keys, and migrations |
| HTTP | Request IDs, `nosniff`, frame denial, referrer policy, and operator CSP |
| Traceability | Structured request logs and authenticated mutation/prediction audit events |
| Lifecycle | Entity deletion removes associated local/S3 objects; maintenance purges audit events and local orphans |
| Container | Non-root runtime and dependency separation |

## Required deployment controls

- TLS for every external connection.
- Secret manager/workload identity and scheduled credential rotation.
- Least-privilege database and S3 identities.
- Private database networking and S3 block-public-access.
- Encrypted backups with tested restore and controlled administrator access.
- Centralized security logs and alerts.
- Image/dependency scanning and an upgrade process.
- Rate limiting and edge request controls appropriate to measured traffic.
- A data-processing purpose, lawful basis/consent where required, and an approved retention schedule.
- A verified process to export or delete a person’s records and every corresponding object/backup according to policy.

## Threat and control summary

| Threat | Existing mitigation | Residual action |
|---|---|---|
| Malicious/oversized image | Byte, format, and pixel validation | Isolate image processing and patch Pillow regularly |
| Filename traversal/overwrite | Server-generated UUID filename | Monitor storage errors and permissions |
| Credential guessing | Authentication and constant-time comparison | Add ingress rate limits, lockout/alerting, and rotation |
| CSRF against operator UI | Same-origin checks | Keep TLS and restrictive Origin handling at proxy |
| Database compromise | API hides embeddings/locators | Encrypt, isolate, patch, monitor, and minimize privileges |
| Public object exposure | Private S3 design and no public URL response | Enforce bucket policy and access analyzer |
| Model misuse | Threshold and explicit no-match | Human review, use restrictions, and independent validation |
| Insider deletion | Audit event and backup expectation | Granular RBAC/approval if organizational risk requires it |
| Denial of service | Upload limits | Add rate limits, concurrency bounds, queueing, and capacity tests |

## Known residual risks

- API-key and HTTP Basic authentication do not provide individual user identity, granular roles, MFA, or session revocation.
- Audit rows share the application database and can be altered by a database administrator.
- Prediction inference is synchronous and has no application-level concurrency queue.
- Stored embeddings are not application-layer encrypted separately from database/storage encryption.
- Object deletion after a database commit can fail, leaving an orphan that needs reconciliation.
- The current readiness check validates S3 configuration, not live S3 access.

These are acceptable for the portfolio scope but must be explicitly accepted or remediated based on a real deployment’s threat model.

## Privacy lifecycle

Before enrolment, define purpose, notice, consent/lawful basis, minimum required samples, retention, permitted operators, and appeal/deletion mechanisms. Use synthetic data for demonstrations. Do not upload real student handwriting to public demos.

When deleting a writer or dataset, verify both SQL records and stored objects are removed. Track deletion failures. Backups should age out under a documented schedule; deletion from live storage does not instantly remove historical backups.

## Responsible use

InkID must not be used as OCR, proof of legal authorship, a forensic conclusion, or the sole basis for grading, discipline, employment, credit, access control, medical decisions, or other high-stakes decisions. A similarity score is not a calibrated probability.
