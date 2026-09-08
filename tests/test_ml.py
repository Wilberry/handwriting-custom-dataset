import numpy as np
import pytest

from app.evaluation import evaluate_embeddings
from app.ml import aggregate_writer_scores


def test_writer_scores_average_each_writers_strongest_samples():
    scores = aggregate_writer_scores(
        similarities=[0.9, 0.7, 0.1, 0.8],
        student_ids=[1, 1, 1, 2],
        top_k=2,
    )
    assert scores == [
        {"student_id": 1, "score": pytest.approx(0.8)},
        {"student_id": 2, "score": pytest.approx(0.8)},
    ]


def test_leave_one_out_evaluation_separates_distinct_writers():
    records = [
        (1, np.array([1.0, 0.0], dtype=np.float32)),
        (1, np.array([0.95, 0.05], dtype=np.float32)),
        (2, np.array([0.0, 1.0], dtype=np.float32)),
        (2, np.array([0.05, 0.95], dtype=np.float32)),
    ]
    result = evaluate_embeddings(records)
    assert result.evaluated_samples == 4
    assert result.writer_count == 2
    assert result.top1_accuracy == 1.0
    assert result.false_accept_rate == 0.0
    assert result.false_reject_rate == 0.0


def test_evaluation_requires_repeat_samples():
    with pytest.raises(ValueError, match="at least two samples"):
        evaluate_embeddings([(1, np.array([1.0, 0.0], dtype=np.float32))])
