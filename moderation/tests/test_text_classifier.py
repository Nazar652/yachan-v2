import os
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.config import settings
from app.text_classifier import OnnxTextClassifier, count_urls, is_spam, softmax


def test_count_urls():
    assert count_urls("visit http://a.com and https://b.org and www.c.net") == 3
    assert count_urls("no links here") == 0


def test_is_spam_flags_many_links():
    assert is_spam("http://a.com http://b.com http://c.com buy now") is True


def test_is_spam_flags_bare_link():
    assert is_spam("http://spam.example") is True


def test_is_spam_flags_heavy_repetition():
    assert is_spam(("buy " * 20).strip()) is True


def test_is_spam_ignores_normal_text():
    assert is_spam("just a normal reply with one http://link.example inside a real sentence") is False


def test_softmax_sums_to_one():
    result = softmax(np.array([2.0, 1.0], dtype=np.float32))
    assert result.sum() == pytest.approx(1.0)
    assert result[0] > result[1]


def test_classify_maps_score_to_flags():
    session = MagicMock()
    session.run.return_value = [np.array([[-3.0, 3.0]], dtype=np.float32)]  # toxic dominant
    tokenizer = MagicMock()
    tokenizer.encode.return_value = MagicMock(ids=[1, 2], attention_mask=[1, 1])

    verdict = OnnxTextClassifier(session, tokenizer, threshold=0.8).classify("whatever")

    assert verdict["toxic"] is True
    assert verdict["spam"] is False
    assert verdict["scores"]["toxic"] > 0.8


def test_classify_below_threshold_is_not_toxic():
    session = MagicMock()
    session.run.return_value = [np.array([[3.0, -3.0]], dtype=np.float32)]  # not-toxic dominant
    tokenizer = MagicMock()
    tokenizer.encode.return_value = MagicMock(ids=[1], attention_mask=[1])

    verdict = OnnxTextClassifier(session, tokenizer, threshold=0.8).classify("hi")

    assert verdict["toxic"] is False


@pytest.mark.skipif(
    not os.path.exists(settings.toxicity_model_path)
    or not os.path.exists(settings.toxicity_tokenizer_path),
    reason="toxicity model not downloaded",
)
def test_real_model_flags_multilingual_toxicity():
    classifier = OnnxTextClassifier.from_paths(
        settings.toxicity_model_path, settings.toxicity_tokenizer_path, settings.toxicity_threshold
    )

    assert classifier.classify("I hope you die you piece of trash")["toxic"] is True
    assert classifier.classify("щоб ти здох гнида нікчемна")["toxic"] is True
    assert classifier.classify("дякую, гарний пост")["toxic"] is False
