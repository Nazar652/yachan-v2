import io
import os
from unittest.mock import MagicMock

import numpy as np
import pytest
from PIL import Image

from app.classifier import OnnxClassifier, preprocess, verdict_from_scores
from app.config import settings


def _png_bytes(color=(255, 0, 0)):
    buffer = io.BytesIO()
    Image.new("RGB", (12, 8), color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_verdict_sfw_is_safe():
    verdict = verdict_from_scores({"nsfl": 0.1, "nsfw": 0.2, "sfw": 0.7})
    assert verdict["status"] == "safe"
    assert verdict["nsfw_score"] == 0.3
    assert verdict["labels"] == {"nsfl": 0.1, "nsfw": 0.2, "sfw": 0.7}


def test_verdict_nsfw_is_flagged():
    assert verdict_from_scores({"nsfl": 0.1, "nsfw": 0.7, "sfw": 0.2})["status"] == "flagged"


def test_verdict_nsfl_is_blocked():
    assert verdict_from_scores({"nsfl": 0.8, "nsfw": 0.1, "sfw": 0.1})["status"] == "blocked"


def test_preprocess_produces_nchw_float_tensor():
    tensor = preprocess(_png_bytes())
    assert tensor.shape == (1, 3, 224, 224)
    assert tensor.dtype == np.float32
    assert float(tensor.min()) >= 0.0
    assert float(tensor.max()) <= 255.0


def test_onnx_classifier_maps_top_class():
    session = MagicMock()
    session.run.return_value = [np.array([[0.9, 0.05, 0.05]], dtype=np.float32)]

    verdict = OnnxClassifier(session).classify(_png_bytes(), "nsfw")

    assert verdict["status"] == "blocked"  # nsfl dominant
    assert "image" in session.run.call_args.args[1]


@pytest.mark.skipif(
    not os.path.exists(settings.onnx_model_path), reason="onnx model not downloaded"
)
def test_real_model_classifies_gray_as_safe():
    classifier = OnnxClassifier.from_path(settings.onnx_model_path)

    verdict = classifier.classify(_png_bytes((130, 130, 130)), "nsfw")

    assert verdict["status"] == "safe"
    assert set(verdict["labels"]) == {"nsfl", "nsfw", "sfw"}
