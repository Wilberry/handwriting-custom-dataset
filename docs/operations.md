# Operations runbook

## Service indicators

At minimum, monitor:

| Signal | Suggested alert |
|---|---|
| Readiness | Consecutive `/health/ready` failures |
| HTTP errors | Sustained or sudden `5xx` increase |
| Latency | Prediction p95/p99 above the validated service objective |
| Resources | Sustained CPU saturation, memory pressure, or disk exhaustion |
| Database | Connection exhaustion, transaction errors, or backup failure |
| Storage | S3 upload/delete failures or unexpected object growth |
| Security | Repeated `401`/`403`, unusual deletion activity, or secret-access anomalies |

Choose numeric thresholds from load-test baselines; arbitrary thresholds without a baseline are not acceptance evidence.

## Health endpoints

- `/health/live` proves the HTTP process can respond. It does not test dependencies.
- `/health/ready` verifies production security configuration, storage configuration, and a database query. Remove an instance from traffic when readiness fails.

Readiness does not upload a test object to S3 or perform model inference. Synthetic monitoring should periodically exercise those paths using dedicated non-personal test data.

## Logs and request correlation

Application request logs are JSON and include method, path, status, duration, and request ID. Query strings are intentionally excluded. Supply or capture `X-Request-ID` when investigating a client failure. Centralize logs with access controls and a retention period; do not add image bytes, credentials, database URLs, or raw embeddings to logs.

## Audit events

Protected mutations and predictions write audit events containing actor, event type, entity, request ID, timestamp, and JSON details. Review them through `/audit-events/`. Audit writes occur in the application database and are useful for operational traceability, but they are not tamper-proof or independently archived.

## Scheduled maintenance

Run at an interval shorter than the approved audit-retention and orphan-grace objectives:

```bash
python -m app.maintenance \
  --audit-retention-days 365 \
  --orphan-grace-hours 24
```

The command purges expired audit rows and unreferenced old files only when local storage is selected. S3 lifecycle and orphan reconciliation must be managed through the object-storage platform.

## Backup and restore

Back up PostgreSQL using provider snapshots plus point-in-time recovery. Enable S3 versioning/lifecycle according to policy. Database and object storage form one logical dataset; a database restored to an earlier time can reference missing/newer objects.

Quarterly—or at the organization’s required frequency—perform a restore exercise:

1. Restore the database into an isolated environment.
2. Restore or attach the corresponding object version set.
3. apply the application version compatible with that schema;
4. confirm record counts and sample locators;
5. run a known synthetic enrolment/prediction/deletion workflow;
6. record recovery point, recovery duration, discrepancies, and corrective action.

## Common incidents

### Readiness returns 503

1. Read the response detail and correlated logs.
2. Verify production credentials are present without printing their values.
3. Verify `STORAGE_BACKEND` and `S3_BUCKET` configuration.
4. Test database network/DNS/TLS and credentials from an approved diagnostic environment.
5. Keep the instance out of traffic until readiness is stable.

### Sample upload fails

1. Distinguish `422` validation from `5xx` model/storage/database errors.
2. Confirm size, format, and decoded pixel count for `422`.
3. Check disk space for local storage or IAM/KMS/bucket policy for S3.
4. Check model-weight availability and process memory.
5. Search for the request ID and verify no orphan object remains.

### Predictions become slow

1. Compare request rate, prediction latency, CPU, and memory with load-test baselines.
2. Confirm the process is not repeatedly downloading/loading model weights.
3. Check dataset reference count and database query latency.
4. Shed excess load or reduce concurrency before memory exhaustion.
5. For recurring saturation, move inference behind a bounded queue/dedicated service.

### Suspected credential compromise

1. Revoke/rotate the affected API, admin, database, or cloud credential.
2. Review access and audit logs for the exposure window.
3. Contain affected instances and preserve evidence.
4. Assess unauthorized reads, writes, and deletions.
5. Follow the organization’s breach and notification process.

## Decommissioning

Disable traffic and credentials, export only data authorized for retention, delete database and object-storage data according to policy, verify backups expire on schedule, and retain a signed decommission record. Never assume deleting the application instance deletes its database, bucket, snapshots, or logs.
