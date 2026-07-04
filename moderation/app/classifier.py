import io
from typing import Protocol, cast

import numpy as np
import onnxruntime as ort
from PIL import Image

Verdict = dict[str, object]

_LABELS = ("nsfl", "nsfw", "sfw")
_STATUS_BY_LABEL = {"sfw": "safe", "nsfw": "flagged", "nsfl": "blocked"}
_INPUT_SIZE = (224, 224)


def preprocess(data: bytes) -> np.ndarray:
    with Image.open(io.BytesIO(data)) as image:
        rgb = image.convert("RGB").resize(_INPUT_SIZE, Image.Resampling.BILINEAR)

    pixels = np.asarray(rgb, dtype=np.float32)

    return pixels.transpose(2, 0, 1)[np.newaxis, :]


def verdict_from_scores(scores: dict[str, float]) -> Verdict:
    top = max(scores, key=lambda label: scores[label])

    return {
        "status": _STATUS_BY_LABEL[top],
        "nsfw_score": round(1.0 - scores.get("sfw", 0.0), 4),
        "labels": scores,
    }


class Classifier(Protocol):
    def classify(self, data: bytes, mode: str) -> Verdict: ...


class OnnxClassifier:
    def __init__(self, session: ort.InferenceSession):
        self.session = session

    @classmethod
    def from_path(cls, model_path: str) -> "OnnxClassifier":
        return cls(ort.InferenceSession(model_path, providers=["CPUExecutionProvider"]))

    def classify(self, data: bytes, mode: str) -> Verdict:
        outputs = cast(list[np.ndarray], self.session.run(None, {"image": preprocess(data)}))
        probabilities = outputs[0][0]
        scores = {label: float(probabilities[index]) for index, label in enumerate(_LABELS)}

        return verdict_from_scores(scores)
