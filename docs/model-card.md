# Model card

## Model details

| Field | Value |
|---|---|
| Task | Closed-set writer identification with an explicit no-match threshold |
| Feature extractor | Torchvision ResNet-50 with standard pretrained weights |
| Output | 2,048-dimensional float32 image embedding |
| Preprocessing | Torchvision weight-provided inference transforms |
| Similarity | Cosine similarity |
| Writer aggregation | Mean of each writer’s strongest reference scores |
| Decision | Highest writer score accepted when `score >= threshold` |
| Training in this repository | None |

ResNet-50 is a generic natural-image feature extractor. InkID does not fine-tune it for handwriting and does not recognize written text.

## Intended use

The current implementation is intended for education, demonstration, portfolio review, and low-risk experiments with authorized or synthetic data. It can show how reference enrolment, embeddings, similarity ranking, and an abstention threshold fit together.

## Inputs and outputs

Inputs are validated JPEG, PNG, or WebP images. Reference images are associated with a known writer. A query returns:

- whether the threshold produced an accepted match;
- accepted writer ID/name, or `null`;
- best similarity score when compatible references exist;
- up to three ranked candidates;
- a message when there are no references, no compatible embeddings, or no confident match.

Cosine similarity is a relative feature-space score, not a probability, confidence percentage, or proof of identity.

## Evaluation implemented

Run:

```bash
python -m app.evaluation --dataset-id <id>
```

The command performs leave-one-out evaluation using stored compatible embeddings. Each sample is used once as a query while its own reference is excluded. It reports evaluated/skipped sample counts, writer count, top-1 accuracy, a data-derived threshold, false-accept rate, and false-reject rate.

This is a development diagnostic. Evaluating and calibrating on the same enrolled population overstates generalization and does not replace an independently held-out test set.

## Required production evaluation protocol

1. Define the intended population, capture devices, paper types, writing instruments, languages/scripts, and operating conditions.
2. Collect consented data with writer-disjoint development, calibration, and test partitions.
3. Prevent near-duplicate scans and session leakage across partitions.
4. Report writer counts, samples per writer, exclusions, and missing data.
5. Select the threshold only on the calibration partition.
6. Freeze the model/preprocessing/threshold, then evaluate once on the test partition.
7. Report top-1 accuracy, false-accept rate, false-reject rate, ROC/DET behavior, confidence intervals, and rejection rate.
8. Stratify results by relevant capture conditions and demographic groups where lawful and ethically appropriate.
9. Test unknown writers, low-quality images, copied/traced writing, non-handwriting images, and distribution shift.
10. Document human review, error consequences, monitoring, and rollback criteria.

No production metric should be placed in this document until it is backed by a versioned dataset manifest and reproducible evaluation artifact.

## Limitations

- Generic ResNet features may emphasize paper texture, scanning artifacts, layout, or ink characteristics rather than writer style.
- Multiple samples from one session can inflate apparent accuracy.
- Different scanners/cameras and image processing can shift embeddings.
- A threshold calibrated for one population or dataset size may not transfer.
- The top candidate can be wrong even when its similarity is high.
- The system does not detect spoofing, tracing, copied writing, or adversarial images.
- Enrollment errors directly contaminate future predictions.
- Performance may vary across scripts, writing abilities, physical conditions, and capture quality.

## Model/version changes

Stored samples include a model identifier and embedding dimension. A change to weights, preprocessing, architecture, or embedding semantics requires a new identifier, re-embedding references, fresh calibration, and full evaluation. Never reuse the identifier for an incompatible model.

## Prohibited interpretation

Do not describe InkID as handwriting recognition, OCR, signature verification, biometric authentication, authorship proof, or forensic analysis. Do not present its score as a probability.
