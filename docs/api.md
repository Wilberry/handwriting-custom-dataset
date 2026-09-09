# API guide

Interactive OpenAPI documentation is available at `/docs` while the service is running.

## Authentication

REST endpoints for datasets, writers, samples, predictions, and audit events require:

```http
X-API-Key: <API_KEY>
```

Authentication may be unset in development. In `APP_ENV=production`, protected calls fail closed unless `API_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` are all configured. The operator console uses HTTP Basic authentication.

## General behavior

- JSON requests use `Content-Type: application/json`.
- Image endpoints use `multipart/form-data`.
- Collection endpoints accept `offset >= 0` and `1 <= limit <= 200`.
- Clients may send `X-Request-ID`; otherwise the service generates one. The response echoes the accepted/generated value.
- IDs are positive integers. Names are trimmed, cannot be blank, and are limited to 120 characters.

## Endpoints

| Method | Endpoint | Request | Success |
|---|---|---|---|
| `GET` | `/` | — | Service message |
| `GET` | `/health/live` | — | `200` when the process responds |
| `GET` | `/health/ready` | — | `200` when database, storage configuration, and production security checks pass |
| `POST` | `/datasets/` | `{"name":"Class A"}` | `201` dataset |
| `GET` | `/datasets/?offset=0&limit=50` | — | Dataset array |
| `PUT` | `/datasets/{id}` | `{"name":"New name"}` | Updated dataset |
| `DELETE` | `/datasets/{id}` | — | `204` |
| `POST` | `/students/` | `{"name":"Ada","dataset_id":1}` | `201` writer |
| `GET` | `/students/{dataset_id}?offset=0&limit=50` | — | Writer array |
| `PUT` | `/students/{id}` | `{"name":"Grace"}` | Updated writer |
| `DELETE` | `/students/{id}` | — | `204` |
| `POST` | `/samples/{student_id}` | Multipart `file` | `201` sample metadata |
| `GET` | `/samples/?offset=0&limit=50` | — | Sample metadata array |
| `DELETE` | `/samples/{id}` | — | `204` |
| `POST` | `/predict/` | Multipart `dataset_id`, `threshold`, `file` | Prediction response |
| `GET` | `/audit-events/?offset=0&limit=50` | — | Newest-first audit array |
| `DELETE` | `/audit-events/retention?older_than_days=365` | — | Deletion count and cutoff |

## Examples

Create a dataset and writer:

```bash
curl -sS -X POST http://localhost:8000/datasets/ \
  -H "X-API-Key: $INKID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo writers"}'

curl -sS -X POST http://localhost:8000/students/ \
  -H "X-API-Key: $INKID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada","dataset_id":1}'
```

Enrol a reference image:

```bash
curl -sS -X POST http://localhost:8000/samples/1 \
  -H "X-API-Key: $INKID_API_KEY" \
  -F "file=@reference.png;type=image/png"
```

Identify a query:

```bash
curl -sS -X POST http://localhost:8000/predict/ \
  -H "X-API-Key: $INKID_API_KEY" \
  -F "dataset_id=1" \
  -F "threshold=0.75" \
  -F "file=@query.png;type=image/png"
```

Example response:

```json
{
  "match": true,
  "predicted_student_id": 1,
  "predicted_student_name": "Ada",
  "similarity_score": 0.91,
  "top_matches": [
    {
      "student_id": 1,
      "student_name": "Ada",
      "similarity_score": 0.91
    }
  ],
  "message": null
}
```

`match: false` means the best score was below the threshold or no compatible references were available. Ranked candidates can still be present when the threshold is not met; consumers must respect `match` rather than treating the first candidate as accepted.

## Error contract

FastAPI errors use a `detail` field. Common statuses are:

| Status | Meaning |
|---:|---|
| `401` | Missing or incorrect API/admin credential |
| `403` | Cross-origin operator form submission rejected |
| `404` | Dataset, writer, or sample not found |
| `409` | Duplicate dataset name or writer name within a dataset |
| `422` | Invalid request, threshold, image format, size, or pixel dimensions |
| `503` | Production security or storage configuration is incomplete |

Do not retry `4xx` responses without changing the request. Retry transient `5xx` responses with bounded exponential backoff and preserve the request ID for support correlation.
