"""Leave-one-out evaluation for enrolled handwriting embeddings."""

import argparse
from dataclasses import asdict, dataclass
import json

import numpy as np

from app import models
from app.database import SessionLocal
from app.ml import EMBEDDING_DIMENSION, EMBEDDING_MODEL, aggregate_writer_scores, compare_embeddings


@dataclass(frozen=True)
class EvaluationResult:
    evaluated_samples: int
    skipped_samples: int
    writer_count: int
    top1_accuracy: float
    calibrated_threshold: float
    false_accept_rate: float
    false_reject_rate: float


def _rates(genuine_scores, impostor_scores, threshold):
    false_rejects = sum(score < threshold for score in genuine_scores)
    false_accepts = sum(score >= threshold for score in impostor_scores)
    frr = false_rejects / len(genuine_scores) if genuine_scores else 0.0
    far = false_accepts / len(impostor_scores) if impostor_scores else 0.0
    return far, frr


def calibrate_threshold(genuine_scores, impostor_scores):
    """Choose the observed threshold where FAR and FRR are closest."""
    candidates = sorted({-1.0, 1.0, *genuine_scores, *impostor_scores})
    return min(
        candidates,
        key=lambda threshold: (
            abs(
                _rates(genuine_scores, impostor_scores, threshold)[0]
                - _rates(genuine_scores, impostor_scores, threshold)[1]
            ),
            -threshold,
        ),
    )


def evaluate_embeddings(records):
    """Evaluate writer identification by holding out each enrolled sample once."""
    normalized = [(int(student_id), np.asarray(embedding)) for student_id, embedding in records]
    writer_counts = {
        student_id: sum(record_id == student_id for record_id, _ in normalized)
        for student_id, _ in normalized
    }
    genuine_scores = []
    impostor_scores = []
    correct = 0
    skipped = 0

    for index, (true_student_id, query) in enumerate(normalized):
        if writer_counts[true_student_id] < 2:
            skipped += 1
            continue
        candidates = normalized[:index] + normalized[index + 1 :]
        embeddings = [embedding for _, embedding in candidates]
        student_ids = [student_id for student_id, _ in candidates]
        scores = aggregate_writer_scores(compare_embeddings(query, embeddings), student_ids)
        by_student = {item["student_id"]: item["score"] for item in scores}
        genuine_scores.append(by_student[true_student_id])
        other_scores = [
            score for student_id, score in by_student.items() if student_id != true_student_id
        ]
        if other_scores:
            impostor_scores.append(max(other_scores))
        if scores[0]["student_id"] == true_student_id:
            correct += 1

    evaluated = len(genuine_scores)
    if not evaluated:
        raise ValueError("Evaluation requires at least two samples for one writer")
    threshold = calibrate_threshold(genuine_scores, impostor_scores)
    far, frr = _rates(genuine_scores, impostor_scores, threshold)
    return EvaluationResult(
        evaluated_samples=evaluated,
        skipped_samples=skipped,
        writer_count=len(writer_counts),
        top1_accuracy=correct / evaluated,
        calibrated_threshold=float(threshold),
        false_accept_rate=far,
        false_reject_rate=frr,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-id", type=int, required=True)
    args = parser.parse_args()

    with SessionLocal() as db:
        samples = (
            db.query(models.HandwritingSample)
            .filter(models.HandwritingSample.embedding_model == EMBEDDING_MODEL)
            .filter(models.HandwritingSample.embedding_dimension == EMBEDDING_DIMENSION)
            .join(models.Student)
            .filter(models.Student.dataset_id == args.dataset_id)
            .all()
        )
        records = [
            (sample.student_id, np.frombuffer(sample.embedding, dtype=np.float32))
            for sample in samples
        ]
    print(json.dumps(asdict(evaluate_embeddings(records)), indent=2))


if __name__ == "__main__":
    main()
