"""
Machine Learning Utilities Module

This module provides machine learning functions for handwriting recognition.
It uses ResNet50 for feature extraction and cosine similarity for comparison.
"""

import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load pretrained ResNet50 model without final classifier
model = models.resnet50(pretrained=True)
model.fc = torch.nn.Identity()  # Remove classification layer to get feature vectors
model.eval()  # Set to evaluation mode

# Image preprocessing pipeline
transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Resize to ResNet50 input size
    transforms.ToTensor(),  # Convert PIL image to tensor
])


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
    # Load and prepare image
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0)  # Add batch dimension
    
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
        similarity = cosine_similarity(
            new_embedding.reshape(1, -1),
            emb.reshape(1, -1)
        )[0][0]
        similarities.append(similarity)
    
    return similarities
