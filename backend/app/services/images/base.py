from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import settings


def image_hash(prompt: str, model: str, aspect_ratio: str, seed: int, style: str) -> str:
    payload = f"{prompt}|{model}|{aspect_ratio}|{seed}|{style}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class ImageProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, dest: Path, *, aspect_ratio: str, seed: int, style: str) -> Path:
        raise NotImplementedError


class LocalImageModel(ImageProvider):
    name = "local"

    def generate(self, prompt: str, dest: Path, *, aspect_ratio: str, seed: int, style: str) -> Path:
        dest.write_bytes(_placeholder_png())
        return dest


def _placeholder_png() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
        b"\xc0\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def get_image_provider() -> ImageProvider:
    from app.services.images.gemini import GeminiImage

    name = settings.image_provider.lower()
    if name == "gemini":
        return GeminiImage()
    if name == "flux":
        from app.services.images.flux import FluxImage

        return FluxImage()
    return LocalImageModel()
