# InkID documentation

This documentation describes the system that exists in this repository. InkID is a writer-identification service: it compares a submitted handwriting image with enrolled reference images and ranks likely writers. It does not transcribe handwriting and does not train a custom model.

## Documentation map

| Document | Audience | Contents |
|---|---|---|
| [Architecture](architecture.md) | Engineers and reviewers | Components, data flow, persistence, boundaries, and design decisions |
| [API guide](api.md) | API consumers | Authentication, endpoints, examples, responses, and errors |
| [Deployment](deployment.md) | Platform engineers | Environment configuration, migrations, PostgreSQL, S3, containers, and rollout |
| [Operations runbook](operations.md) | Operators | Health, logs, audit, maintenance, backup, restore, incidents, and rollback |
| [Security and privacy](security-privacy.md) | Owners and reviewers | Threat controls, data classification, retention, and residual risks |
| [Model card](model-card.md) | ML reviewers and product owners | Model purpose, scoring, evaluation, limitations, and prohibited uses |
| [Testing](testing.md) | Contributors | Test strategy, commands, coverage, and missing environment tests |
| [Production checklist](production-checklist.md) | Release owners | Evidence-based go-live and rollback checklist |

## Status vocabulary

- **Implemented** means the behavior is present in the repository and covered by local verification where practical.
- **Configured at deployment** means the code supports it, but credentials or managed services must be supplied by an operator.
- **Requires external evidence** means it cannot honestly be completed without representative data, policy approval, or a live environment.

The repository is suitable as a portfolio-grade working service. A production launch is not approved solely because the application starts; every mandatory item in the production checklist must have an owner and evidence.
