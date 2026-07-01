import io
import secrets
import uuid

from PIL import Image, ImageDraw

# omit ambiguous characters (0/O, 1/I) to reduce misreads
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_DEFAULT_LENGTH = 5

# match the frontend's surface-2/text design tokens (frontend/src/assets/main.css)
# so the rendered image blends into its box instead of showing a plain white tile
_LIGHT_BACKGROUND = "#e8ddc4"
_LIGHT_FOREGROUND = "#2a2018"
_DARK_BACKGROUND = "#2b2316"
_DARK_FOREGROUND = "#efe5cf"


def new_token() -> str:
    return uuid.uuid4().hex


def generate_answer(length: int = _DEFAULT_LENGTH) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def render_image(text: str, background: str, foreground: str) -> bytes:
    image = Image.new("RGB", (140, 50), background)
    draw = ImageDraw.Draw(image)
    draw.text((15, 15), " ".join(text), fill=foreground)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def render_image_pair(text: str) -> tuple[bytes, bytes]:
    """Returns (light png, dark png) rendered for the same answer."""
    return (
        render_image(text, _LIGHT_BACKGROUND, _LIGHT_FOREGROUND),
        render_image(text, _DARK_BACKGROUND, _DARK_FOREGROUND),
    )
