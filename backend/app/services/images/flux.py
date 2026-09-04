from __future__ import annotations

from pathlib import Path

from app.services.images.base import ImageProvider, LocalImageModel


class FluxImage(ImageProvider):
    name = "flux"

    def generate(self, prompt: str, dest: Path, *, aspect_ratio: str, seed: int, style: str) -> Path:
        return LocalImageModel().generate(prompt, dest, aspect_ratio=aspect_ratio, seed=seed, style=style)
