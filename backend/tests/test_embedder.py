"""
Unit tests for Ojas Embedder module (backend/app/rag/embedder.py).
"""

import pytest

from backend.app.rag.embedder import Embedder, get_embedder, EMBEDDING_DIMENSION


def test_embedder_singleton():
    emb1 = get_embedder()
    emb2 = get_embedder()
    assert emb1 is emb2
    assert emb1.is_available


def test_embed_single():
    embedder = get_embedder()
    vector = embedder.embed_single("Software requirement for user authentication")
    assert isinstance(vector, list)
    assert len(vector) == EMBEDDING_DIMENSION
    assert all(isinstance(x, float) for x in vector)
    # Ensure vector is non-zero
    assert any(x != 0.0 for x in vector)


def test_embed_texts_batch():
    embedder = get_embedder()
    texts = [
        "First requirement: login API endpoint",
        "Second requirement: password reset via email",
        "Third requirement: database migration scripts",
    ]
    vectors = embedder.embed_texts(texts)
    assert len(vectors) == 3
    for v in vectors:
        assert len(v) == EMBEDDING_DIMENSION


def test_embed_empty():
    embedder = get_embedder()
    assert embedder.embed_texts([]) == []


def test_semantic_similarity_relative():
    """Verify related texts have higher dot product/similarity than unrelated texts."""
    import math

    embedder = get_embedder()
    v_login = embedder.embed_single("User login and authentication via credentials")
    v_auth = embedder.embed_single("Sign-in system and JWT authentication tokens")
    v_fruit = embedder.embed_single("Tropical fruit cultivation in organic orchards")

    def dot_product(v1, v2):
        return sum(a * b for a, b in zip(v1, v2))

    def norm(v):
        return math.sqrt(sum(a * a for a in v))

    def cosine_sim(v1, v2):
        return dot_product(v1, v2) / (norm(v1) * norm(v2))

    sim_related = cosine_sim(v_login, v_auth)
    sim_unrelated = cosine_sim(v_login, v_fruit)

    assert sim_related > sim_unrelated
