from typing import Protocol

# the verdict json shape sent back to yachan (see docs/moderation-contract.md)
Verdict = dict[str, object]

_BLOCKED_LABELS = frozenset({"porn", "hentai"})
_FLAGGED_LABELS = frozenset({"sexy"})


def status_from_labels(scores: dict[str, float]) -> str:
    # top-scoring class decides the tier: porn/hentai block, sexy flags, rest safe
    top = max(scores, key=lambda label: scores[label])
    if top in _BLOCKED_LABELS:
        return "blocked"
    if top in _FLAGGED_LABELS:
        return "flagged"
    return "safe"


class Classifier(Protocol):
    def classify(self, data: bytes, mode: str) -> Verdict: ...


class StubClassifier:
    """Placeholder until the real multi-class NSFW model lands (step 3b); marks
    everything safe so the transport can run end-to-end without torch."""

    def classify(self, data: bytes, mode: str) -> Verdict:
        return {"status": "safe", "nsfw_score": 0.0, "labels": None}
