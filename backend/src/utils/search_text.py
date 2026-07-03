import re

# strip imageboard/markdown noise so the embedding sees words, not syntax:
# post refs (>>123), emphasis/spoiler/code markers, greentext arrows
_POST_REF = re.compile(r">>\d+")
_MARKUP = re.compile(r"\*\*|__|~~|%%|\^\^|```|`|\*|_|\^|>")
_WHITESPACE = re.compile(r"\s+")


def clean_search_text(text: str) -> str:
    text = _POST_REF.sub(" ", text)
    text = _MARKUP.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip()
