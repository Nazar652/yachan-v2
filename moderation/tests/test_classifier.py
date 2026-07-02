from app.classifier import StubClassifier, status_from_labels


def test_status_blocked_for_porn():
    assert status_from_labels({"porn": 0.9, "neutral": 0.1}) == "blocked"


def test_status_blocked_for_hentai():
    assert status_from_labels({"hentai": 0.8, "sexy": 0.2}) == "blocked"


def test_status_flagged_for_sexy():
    assert status_from_labels({"sexy": 0.7, "neutral": 0.3}) == "flagged"


def test_status_safe_for_neutral():
    assert status_from_labels({"neutral": 0.9, "porn": 0.1}) == "safe"


def test_stub_classifier_marks_safe():
    assert StubClassifier().classify(b"x", "nsfw") == {
        "status": "safe",
        "nsfw_score": 0.0,
        "labels": None,
    }
