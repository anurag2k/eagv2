import numpy as np
from scipy.spatial.distance import cosine
import requests
import json

def get_embedding(text: str) -> np.ndarray:
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": "nomic-embed-text",
            "prompt": text
        }
    )
    response.raise_for_status()
    return np.array(response.json()["embedding"], dtype=np.float32)

# Phrases to compare
sentences = [
    "How does AlphaFold work?",
    "How do proteins fold?",
    "What is the capital of France?",
    "Explain how neural networks learn."
]

# Get embeddings
embeddings = [get_embedding(s) for s in sentences]

# Compare all pairs using cosine similarity
def cosine_similarity(v1, v2):
    return 1 - cosine(v1, v2)  # 1 = perfect match

print(" Semantic Similarity Matrix:\n")
for i in range(len(sentences)):
    for j in range(i + 1, len(sentences)):
        sim = cosine_similarity(embeddings[i], embeddings[j])
        print(f"\"{sentences[i]}\" ↔ \"{sentences[j]}\" → similarity = {sim:.3f}")
