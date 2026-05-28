import io
import secrets
import uuid

from PIL import Image, ImageDraw

# omit ambiguous characters (0/O, 1/I) to reduce misreads
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_DEFAULT_LENGTH = 5


def new_token() -> str:
    return uuid.uuid4().hex


def generate_answer(length: int = _DEFAULT_LENGTH) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def render_image(text: str) -> bytes:
    image = Image.new("RGB", (140, 50), "white")
    draw = ImageDraw.Draw(image)
    draw.text((15, 15), " ".join(text), fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
