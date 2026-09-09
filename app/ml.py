"""
Machine Learning Utilities Module

This module provides machine learning functions for handwriting recognition.
It uses ResNet50 for feature extraction and cosine similarity for comparison.
"""

from functools import lru_cache
from collections import defaultdict

from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

EMBEDDING_MODEL = "torchvision/resnet50:IMAGENET1K_V2"
EMBEDDING_DIMENSION = 2048


@lru_cache(maxsize=1)
def load_feature_extractor():
    """Load the pretrained model lazily and use its canonical preprocessing."""
    import torch
    from torchvision.models import ResNet50_Weights, resnet50

    weights = ResNet50_Weights.DEFAULT
    model = resnet50(weights=weights)
    model.fc = torch.nn.Identity()
    model.eval()
    return model, weights.transforms()


def extract_embedding(image_path: str):
    """
    Extract a feature embedding from a handwriting image.

    Uses a pretrained ResNet50 model to extract high-dimensional feature vectors
    from handwriting images. These embeddings can be used for comparison and classification.

    Args:
        image_path (str): Path to the handwriting image file.

    Returns:
        np.ndarray: 1D numpy array containing the embedding vector (2048 dimensions).
    """
    import torch

    model, preprocess = load_feature_extractor()
    with Image.open(image_path) as source:
        image = preprocess(source.convert("RGB")).unsqueeze(0)

    # Extract embedding using model
    with torch.no_grad():
        embedding = model(image)

    # Convert tensor to numpy array
    embedding = embedding.squeeze().numpy()
    return embedding


def compare_embeddings(new_embedding, stored_embeddings):
    """
    Compare a new embedding against a list of stored embeddings.

    Computes cosine similarity between the new embedding and each stored embedding.
    Higher similarity scores indicate more similar handwriting patterns.

    Args:
        new_embedding (np.ndarray): The embedding to compare (1D array).
        stored_embeddings (list[np.ndarray]): List of stored embeddings to compare against.

    Returns:
        list[float]: Cosine similarity scores for each stored embedding, in range [0, 1].
    """
    similarities = []

    # Compute similarity with each stored embedding
    for emb in stored_embeddings:
        similarity = cosine_similarity(new_embedding.reshape(1, -1), emb.reshape(1, -1))[0][0]
        similarities.append(similarity)

    return similarities


def aggregate_writer_scores(similarities, student_ids, top_k: int = 3):
    """Aggregate sample similarities into stable per-writer scores.

    Averaging the strongest few samples prevents writers with more enrolled
    samples from gaining an unfair advantage while reducing single-sample noise.
    """
    if len(similarities) != len(student_ids):
        raise ValueError("Similarities and student IDs must have equal lengths")
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    grouped = defaultdict(list)
    for similarity, student_id in zip(similarities, student_ids, strict=True):
        grouped[int(student_id)].append(float(similarity))

    writer_scores = []
    for student_id, scores in grouped.items():
        strongest = sorted(scores, reverse=True)[:top_k]
        writer_scores.append({"student_id": student_id, "score": sum(strongest) / len(strongest)})
    return sorted(writer_scores, key=lambda item: item["score"], reverse=True)
