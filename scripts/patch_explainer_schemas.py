#!/usr/bin/env python3
"""Add reel_mode + DiagramStep to API/lesson schemas."""
from pathlib import Path

ROOT = Path("/Users/pravinkhalase/Desktop/Pravin/cursor/ai-coder")

# ---- api.py ----
api = ROOT / "backend/app/schemas/api.py"
text = api.read_text(encoding="utf-8")
if "reel_mode" not in text:
    text = text.replace(
        "    reel_seconds: int = 30\n    requires_code: bool | None = None\n",
        "    reel_seconds: int = 30\n"
        "    requires_code: bool | None = None\n"
        "    reel_mode: str | None = None\n",
        1,
    )
    # Insert validator after reel_seconds validator
    marker = (
        '    @field_validator("reel_seconds")\n'
        "    @classmethod\n"
        "    def _reel_seconds(cls, value: int) -> int:\n"
        "        return normalize_reel_seconds(value)\n"
    )
    addition = (
        marker
        + "\n"
        + '    @field_validator("reel_mode")\n'
        + "    @classmethod\n"
        + "    def _reel_mode(cls, value: str | None) -> str | None:\n"
        + "        if value is None:\n"
        + "            return None\n"
        + "        cleaned = str(value).strip().lower()\n"
        + '        if cleaned not in {"code", "info", "explainer"}:\n'
        + '            raise ValueError(\'reel_mode must be "code", "info", "explainer", or null\')\n'
        + "        return cleaned\n"
    )
    if marker not in text:
        raise SystemExit("api.py reel_seconds validator missing")
    if '_reel_mode' not in text:
        text = text.replace(marker, addition, 1)
    api.write_text(text, encoding="utf-8")
    print("api.py ok")
else:
    print("api.py already has reel_mode")

# ---- lesson.py ----
lesson = ROOT / "backend/app/schemas/lesson.py"
lt = lesson.read_text(encoding="utf-8")

if "class DiagramStep" not in lt:
    lt = lt.replace(
        "class ConceptScene(BaseScene):\n"
        '    type: Literal["concept"] = "concept"\n'
        '    concept_id: str = "for_loop"\n'
        "    bullets: list[str] = Field(default_factory=list, max_length=8)\n",
        "class DiagramStep(BaseModel):\n"
        "    title: str = Field(min_length=1, max_length=120)\n"
        '    detail: str = Field(default="", max_length=240)\n'
        "\n"
        "\n"
        "class ConceptScene(BaseScene):\n"
        '    type: Literal["concept"] = "concept"\n'
        '    concept_id: str = "for_loop"\n'
        "    bullets: list[str] = Field(default_factory=list, max_length=8)\n"
        "    diagram_steps: list[DiagramStep] = Field(default_factory=list, max_length=8)\n",
        1,
    )
    print("DiagramStep + ConceptScene.diagram_steps ok")
else:
    print("DiagramStep already present")

# reel_mode on TutorPlan
if "reel_mode" not in lt[lt.index("class TutorPlan"): lt.index("class Lesson")]:
    lt = lt.replace(
        "    reel_seconds: int = 30\n"
        "    requires_code: bool = True\n"
        "\n"
        '    @field_validator("spoken_language")\n'
        "    @classmethod\n"
        "    def _spoken(cls, value: str) -> str:\n"
        "        return normalize_spoken_language(value)\n"
        "\n"
        '    @field_validator("reel_seconds")\n'
        "    @classmethod\n"
        "    def _reel_seconds(cls, value: int) -> int:\n"
        "        return normalize_reel_seconds(value)\n"
        "\n"
        "\n"
        "class Lesson(BaseModel):",
        "    reel_seconds: int = 30\n"
        "    requires_code: bool = True\n"
        "    reel_mode: str | None = None\n"
        "\n"
        '    @field_validator("spoken_language")\n'
        "    @classmethod\n"
        "    def _spoken(cls, value: str) -> str:\n"
        "        return normalize_spoken_language(value)\n"
        "\n"
        '    @field_validator("reel_seconds")\n'
        "    @classmethod\n"
        "    def _reel_seconds(cls, value: int) -> int:\n"
        "        return normalize_reel_seconds(value)\n"
        "\n"
        '    @field_validator("reel_mode")\n'
        "    @classmethod\n"
        "    def _reel_mode(cls, value: str | None) -> str | None:\n"
        "        if value is None:\n"
        "            return None\n"
        "        cleaned = str(value).strip().lower()\n"
        '        if cleaned not in {"code", "info", "explainer"}:\n'
        '            raise ValueError(\'reel_mode must be "code", "info", "explainer", or null\')\n'
        "        return cleaned\n"
        "\n"
        "\n"
        "class Lesson(BaseModel):",
        1,
    )
    print("TutorPlan.reel_mode ok")

# reel_mode on Lesson
lesson_block_start = lt.index("class Lesson(BaseModel):")
lesson_block_end = lt.index("class GenericScene")
lesson_chunk = lt[lesson_block_start:lesson_block_end]
if "reel_mode" not in lesson_chunk:
    lt = lt.replace(
        "    reel_seconds: int = 30\n"
        "    requires_code: bool = True\n"
        "\n"
        '    @field_validator("language")\n',
        "    reel_seconds: int = 30\n"
        "    requires_code: bool = True\n"
        "    reel_mode: str | None = None\n"
        "\n"
        '    @field_validator("language")\n',
        1,
    )
    # Add validator after reel_seconds on Lesson — before _copy_code_forward
    if 'def _reel_mode(cls, value: str | None)' not in lt[lt.index("class Lesson(BaseModel):"):lt.index("class GenericScene")]:
        lt = lt.replace(
            '    @field_validator("reel_seconds")\n'
            "    @classmethod\n"
            "    def _reel_seconds(cls, value: int) -> int:\n"
            "        return normalize_reel_seconds(value)\n"
            "\n"
            "    @model_validator(mode=\"before\")\n"
            "    @classmethod\n"
            "    def _copy_code_forward",
            '    @field_validator("reel_seconds")\n'
            "    @classmethod\n"
            "    def _reel_seconds(cls, value: int) -> int:\n"
            "        return normalize_reel_seconds(value)\n"
            "\n"
            '    @field_validator("reel_mode")\n'
            "    @classmethod\n"
            "    def _reel_mode(cls, value: str | None) -> str | None:\n"
            "        if value is None:\n"
            "            return None\n"
            "        cleaned = str(value).strip().lower()\n"
            '        if cleaned not in {"code", "info", "explainer"}:\n'
            '            raise ValueError(\'reel_mode must be "code", "info", "explainer", or null\')\n'
            "        return cleaned\n"
            "\n"
            "    @model_validator(mode=\"before\")\n"
            "    @classmethod\n"
            "    def _copy_code_forward",
            1,
        )
    print("Lesson.reel_mode ok")
else:
    print("Lesson.reel_mode already present")

# GenericScene diagram_steps
gen_start = lt.index("class GenericScene")
gen_end = lt.index("class LessonDraft")
if "diagram_steps" not in lt[gen_start:gen_end]:
    lt = lt.replace(
        '    concept_id: str = "for_loop"\n'
        "\n"
        "\n"
        "class LessonDraft",
        '    concept_id: str = "for_loop"\n'
        "    diagram_steps: list[DiagramStep] = Field(default_factory=list, max_length=8)\n"
        "\n"
        "\n"
        "class LessonDraft",
        1,
    )
    print("GenericScene.diagram_steps ok")

# LessonDraft reel_mode
draft_start = lt.index("class LessonDraft")
draft_end = lt.index("def fallback_example_code")
if "reel_mode" not in lt[draft_start:draft_end]:
    lt = lt.replace(
        "    reel_seconds: int = 30\n"
        "    requires_code: bool = True\n"
        "\n"
        '    @field_validator("spoken_language")\n'
        "    @classmethod\n"
        "    def _spoken(cls, value: str) -> str:\n"
        "        return normalize_spoken_language(value)\n"
        "\n"
        '    @field_validator("reel_seconds")\n'
        "    @classmethod\n"
        "    def _reel_seconds(cls, value: int) -> int:\n"
        "        return normalize_reel_seconds(value)\n"
        "\n"
        "\n"
        "def fallback_example_code",
        "    reel_seconds: int = 30\n"
        "    requires_code: bool = True\n"
        "    reel_mode: str | None = None\n"
        "\n"
        '    @field_validator("spoken_language")\n'
        "    @classmethod\n"
        "    def _spoken(cls, value: str) -> str:\n"
        "        return normalize_spoken_language(value)\n"
        "\n"
        '    @field_validator("reel_seconds")\n'
        "    @classmethod\n"
        "    def _reel_seconds(cls, value: int) -> int:\n"
        "        return normalize_reel_seconds(value)\n"
        "\n"
        "\n"
        "def fallback_example_code",
        1,
    )
    print("LessonDraft.reel_mode ok")

lesson.write_text(lt, encoding="utf-8")
print("lesson.py written")
