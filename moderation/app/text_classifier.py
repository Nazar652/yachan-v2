import re
from typing import Protocol

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

Verdict = dict[str, object]

_MAX_TOKENS = 256
_URL_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)


def count_urls(text: str) -> int:
    return len(_URL_PATTERN.findall(text))


def is_spam(text: str) -> bool:
    # only blatant spam: a wall of links, a link with almost no text around it, or
    # the same token hammered over and over
    urls = count_urls(text)
    if urls >= 3:
        return True

    words = text.split()
    if urls >= 1 and len(words) <= 3:
        return True

    if words:
        top_count = max(words.count(word) for word in set(words))
        if top_count >= 10 and top_count / len(words) > 0.5:
            return True

    return False


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = np.exp(logits - logits.max())
    return shifted / shifted.sum()


class TextClassifier(Protocol):
    def classify(self, text: str) -> Verdict: ...


class OnnxTextClassifier:
    def __init__(self, session: ort.InferenceSession, tokenizer: Tokenizer, threshold: float):
        self.session = session
        self.tokenizer = tokenizer
        self.threshold = threshold

    @classmethod
    def from_paths(
        cls, model_path: str, tokenizer_path: str, threshold: float
    ) -> "OnnxTextClassifier":
        session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        tokenizer = Tokenizer.from_file(tokenizer_path)
        tokenizer.enable_truncation(max_length=_MAX_TOKENS)

        return cls(session, tokenizer, threshold)

    def toxicity_score(self, text: str) -> float:
        encoding = self.tokenizer.encode(text)
        input_ids = np.array([encoding.ids], dtype=np.int64)
        attention_mask = np.array([encoding.attention_mask], dtype=np.int64)
        logits = np.asarray(
            self.session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})[0]
        )[0]
        return float(softmax(logits)[1])

    def classify(self, text: str) -> Verdict:
        score = self.toxicity_score(text)

        return {
            "toxic": score >= self.threshold,
            "spam": is_spam(text),
            "scores": {"toxic": round(score, 4)},
        }
