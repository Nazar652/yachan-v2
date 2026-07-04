import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from src.core.config import get_settings
from src.core.embeddings import EmbeddingModel, l2_normalize, mean_pool


def test_mean_pool_averages_over_tokens():
    token_embeddings = np.array([[1.0, 1.0], [3.0, 3.0]], dtype=np.float32)
    pooled = mean_pool(token_embeddings, [1, 1])
    assert pooled.tolist() == [2.0, 2.0]


def test_mean_pool_ignores_padded_tokens():
    token_embeddings = np.array([[2.0, 2.0], [100.0, 100.0]], dtype=np.float32)
    pooled = mean_pool(token_embeddings, [1, 0])
    assert pooled.tolist() == [2.0, 2.0]


def test_l2_normalize_returns_unit_vector():
    normalized = l2_normalize(np.array([3.0, 4.0], dtype=np.float32))
    assert normalized.tolist() == pytest.approx([0.6, 0.8])


def test_l2_normalize_zero_vector_stays_zero():
    normalized = l2_normalize(np.zeros(3, dtype=np.float32))
    assert normalized.tolist() == [0.0, 0.0, 0.0]


def test_embed_runs_session_and_returns_normalized_vector():
    tokenizer = MagicMock()
    tokenizer.encode.return_value = SimpleNamespace(ids=[5, 6], attention_mask=[1, 1])
    session = MagicMock()
    session.run.return_value = [np.array([[[3.0, 4.0], [3.0, 4.0]]], dtype=np.float32)]

    vector = EmbeddingModel(session, tokenizer).embed("hello")

    assert vector == pytest.approx([0.6, 0.8])
    feed = session.run.call_args.args[1]
    assert set(feed) == {"input_ids", "attention_mask", "token_type_ids"}


def test_from_paths_caps_intra_op_threads(monkeypatch):
    options = MagicMock()
    monkeypatch.setattr("src.core.embeddings.ort.SessionOptions", MagicMock(return_value=options))
    session_factory = MagicMock()
    monkeypatch.setattr("src.core.embeddings.ort.InferenceSession", session_factory)
    monkeypatch.setattr("src.core.embeddings.Tokenizer.from_file", MagicMock(return_value=MagicMock()))

    EmbeddingModel.from_paths("model.onnx", "tokenizer.json")

    assert options.intra_op_num_threads == 1
    session_factory.assert_called_once_with(
        "model.onnx", sess_options=options, providers=["CPUExecutionProvider"]
    )


@pytest.mark.skipif(
    not os.path.exists(get_settings().embedding_model_path)
    or not os.path.exists(get_settings().embedding_tokenizer_path),
    reason="embedding model not downloaded",
)
def test_real_model_orders_similar_text_closer():
    settings = get_settings()
    model = EmbeddingModel.from_paths(
        settings.embedding_model_path, settings.embedding_tokenizer_path
    )

    anchor = np.array(model.embed("a cat sleeps on the sofa"))
    similar = np.array(model.embed("the kitten is napping on the couch"))
    different = np.array(model.embed("stock markets fell sharply today"))

    assert len(anchor) == 384
    assert float(anchor @ similar) > float(anchor @ different)
