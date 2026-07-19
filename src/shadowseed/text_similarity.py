"""Language-agnostic text tokenization and deterministic lexical similarity."""

from __future__ import annotations

import re

import numpy as np

from shadowseed.hash_utils import stable_bucket_index

STOPWORDS = {
    "de", "het", "een", "en", "of", "van", "in", "op", "te", "is", "zijn", "was",
    "met", "als", "voor", "bij", "door", "naar", "uit", "aan", "this", "that", "the",
    "and", "or", "of", "in", "on", "to", "a", "an", "is", "are", "was", "were", "with",
    "for", "by", "as", "at", "from",
}


def tokenize(text: str) -> set[str]:
    """Return normalized content tokens for English and Dutch benchmark text."""

    words = re.findall(r"[A-Za-zÀ-ÿ0-9_]+", text.lower())
    return {word for word in words if word not in STOPWORDS and len(word) > 2}


def lexical_embedding(text: str, dimensions: int = 128) -> np.ndarray:
    """Create a deterministic hashed bag-of-words vector."""

    vector = np.zeros(dimensions, dtype=float)
    for token in tokenize(text):
        vector[stable_bucket_index(token, dimensions)] += 1.0
    return vector


def jaccard(left: str, right: str) -> float:
    """Compute token-set Jaccard similarity."""

    left_tokens = tokenize(left)
    right_tokens = tokenize(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
