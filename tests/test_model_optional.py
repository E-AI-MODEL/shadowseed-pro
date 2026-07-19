import pytest

pytest.importorskip("sentence_transformers")

from shadowseed.manager import SSLManager


def test_real_embedding_smoke():
    manager = SSLManager()
    emb = manager.get_embedding("test zin voor embedding")
    assert emb is not None
    assert hasattr(emb, "shape")
