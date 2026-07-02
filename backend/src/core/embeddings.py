from functools import lru_cache

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from src.core.config import get_settings

# sentence-transformers MiniLM truncates at 128 tokens; longer post bodies are cut
_MAX_TOKENS = 128


def mean_pool(token_embeddings: np.ndarray, attention_mask: list[int]) -> np.ndarray:
    mask = np.array(attention_mask, dtype=np.float32)[:, np.newaxis]
    summed = (token_embeddings * mask).sum(axis=0)
    counts = np.clip(mask.sum(axis=0), a_min=1e-9, a_max=None)
    return summed / counts


def l2_normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        return vector
    return vector / norm


class EmbeddingModel:
    def __init__(self, session: ort.InferenceSession, tokenizer: Tokenizer) -> None:
        self.session = session
        self.tokenizer = tokenizer

    @classmethod
    def from_paths(cls, model_path: str, tokenizer_path: str) -> EmbeddingModel:
        session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        tokenizer = Tokenizer.from_file(tokenizer_path)
        tokenizer.enable_truncation(max_length=_MAX_TOKENS)
        return cls(session, tokenizer)

    def embed(self, text: str) -> list[float]:
        encoding = self.tokenizer.encode(text)
        input_ids = np.array([encoding.ids], dtype=np.int64)
        attention_mask = np.array([encoding.attention_mask], dtype=np.int64)
        feed = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": np.zeros_like(input_ids),
        }
        last_hidden_state = np.asarray(self.session.run(None, feed)[0])
        pooled = mean_pool(last_hidden_state[0], encoding.attention_mask)
        return l2_normalize(pooled).tolist()


@lru_cache
def get_embedding_model() -> EmbeddingModel:
    settings = get_settings()
    return EmbeddingModel.from_paths(settings.embedding_model_path, settings.embedding_tokenizer_path)
