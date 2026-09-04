from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class LessonLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class SceneType(str, Enum):
    intro = "intro"
    concept = "concept"
    code = "code"
    execution = "execution"
    terminal = "terminal"
    quiz = "quiz"
    summary = "summary"


class QuizKind(str, Enum):
    multiple_choice = "multiple_choice"
    predict_output = "predict_output"
    fill_in_code = "fill_in_code"
    find_the_bug = "find_the_bug"
    modify_code = "modify_code"
    explain = "explain"
    coding_challenge = "coding_challenge"


class TutorExpression(str, Enum):
    idle = "idle"
    talking = "talking"
    thinking = "thinking"
    happy = "happy"
    confused = "confused"
    pointing = "pointing"
    explaining = "explaining"
    celebrating = "celebrating"
    listening = "listening"


class HighlightRange(BaseModel):
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    start_col: int = Field(default=0, ge=0)
    end_col: int | None = None
    label: str = Field(min_length=1, max_length=64)
    color: str = Field(default="#f59e0b", max_length=16)

    @model_validator(mode="after")
    def _order(self) -> HighlightRange:
        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")
        return self


class NarrationSegment(BaseModel):
    start: float = Field(ge=0)
    end: float = Field(ge=0.1)
    text: str = Field(min_length=1, max_length=500)
    highlight: str | None = None
    expression: TutorExpression = TutorExpression.explaining
    gesture: str = "point_right"

    @model_validator(mode="after")
    def _span(self) -> NarrationSegment:
        if self.end <= self.start:
            raise ValueError("segment end must be greater than start")
        return self


class VisualSpec(BaseModel):
    kind: str = "none"
    title: str = ""
    callouts: list[str] = Field(default_factory=list)
    particles: bool = False


class VariableSnapshot(BaseModel):
    name: str
    value: str
    type: str = "int"


class ExecutionStep(BaseModel):
    index: int = Field(ge=1)
    label: str
    description: str
    line: int = Field(ge=1)
    condition: str | None = None
    condition_result: bool | None = None
    output_line: str | None = None
    variables: list[VariableSnapshot] = Field(default_factory=list)
    stopped: bool = False


class BaseScene(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    duration: float = Field(ge=0.1, le=120)
    narration: str = Field(min_length=1, max_length=2000)
    segments: list[NarrationSegment] = Field(default_factory=list)
    expression: TutorExpression = TutorExpression.explaining
    visual: VisualSpec = Field(default_factory=VisualSpec)
    audio_url: str | None = None


class IntroScene(BaseScene):
    type: Literal["intro"] = "intro"


class ConceptScene(BaseScene):
    type: Literal["concept"] = "concept"
    concept_id: str = "for_loop"
    bullets: list[str] = Field(default_factory=list, max_length=8)


class CodeScene(BaseScene):
    type: Literal["code"] = "code"
    language: str = "java"
    filename: str = "Main.java"
    code: str = Field(min_length=1, max_length=20_000)
    highlight_ranges: list[HighlightRange] = Field(default_factory=list)
    typing_animation: bool = True


class ExecutionScene(BaseScene):
    type: Literal["execution"] = "execution"
    language: str = "java"
    code: str = Field(min_length=1, max_length=20_000)
    expected_output: list[str] = Field(default_factory=list)
    iterations: list[ExecutionStep] = Field(default_factory=list)
    verified: bool = False


class TerminalScene(BaseScene):
    type: Literal["terminal"] = "terminal"
    command: str = "java Main"
    stdout: list[str] = Field(default_factory=list)
    stderr: str = ""
    success: bool = True
    verified: bool = False


class QuizScene(BaseScene):
    type: Literal["quiz"] = "quiz"
    kind: QuizKind = QuizKind.predict_output
    question: str = Field(min_length=1, max_length=1000)
    code: str | None = None
    options: list[str] = Field(default_factory=list)
    answer: int | str | None = None
    explanation: str = Field(default="", max_length=2000)
    blank_token: str | None = None
    starter_code: str | None = None
    tests: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _quiz_shape(self) -> QuizScene:
        if self.kind in {QuizKind.multiple_choice, QuizKind.predict_output, QuizKind.find_the_bug}:
            if len(self.options) < 2:
                raise ValueError("quiz options require at least 2 choices")
            if not isinstance(self.answer, int):
                raise ValueError("choice quizzes require an integer answer index")
            if self.answer < 0 or self.answer >= len(self.options):
                raise ValueError("answer index out of range")
        return self


class SummaryScene(BaseScene):
    type: Literal["summary"] = "summary"
    takeaways: list[str] = Field(default_factory=list, max_length=8)


LessonScene = Annotated[
    Union[
        IntroScene,
        ConceptScene,
        CodeScene,
        ExecutionScene,
        TerminalScene,
        QuizScene,
        SummaryScene,
    ],
    Field(discriminator="type"),
]


class LessonObjective(BaseModel):
    id: str
    text: str


class TutorPlan(BaseModel):
    language: str = Field(min_length=1, max_length=32)
    level: LessonLevel = LessonLevel.beginner
    topic: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=160)
    skill_assessment: str = Field(default="beginner", max_length=80)
    objectives: list[str] = Field(min_length=1, max_length=8)
    concepts: list[str] = Field(min_length=1, max_length=12)
    greeting: str = Field(min_length=1, max_length=400)


class Lesson(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=160)
    language: str = Field(min_length=1, max_length=32)
    level: LessonLevel = LessonLevel.beginner
    topic: str = Field(min_length=1, max_length=200)
    objectives: list[str] = Field(min_length=1, max_length=8)
    concepts: list[str] = Field(default_factory=list)
    scenes: list[LessonScene] = Field(min_length=3, max_length=24)
    code_examples: list[str] = Field(default_factory=list)

    @field_validator("language")
    @classmethod
    def _lang(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def _required_scene_types(self) -> Lesson:
        types = {scene.type for scene in self.scenes}
        missing = {"intro", "code", "quiz"} - types
        if missing:
            raise ValueError(f"lesson is missing required scenes: {sorted(missing)}")
        return self


class GenericScene(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    type: SceneType
    duration: float = Field(ge=0.1, le=120)
    narration: str = Field(min_length=1, max_length=2000)
    segments: list[NarrationSegment] = Field(default_factory=list)
    expression: TutorExpression = TutorExpression.explaining
    language: str = "java"
    filename: str = "Main.java"
    code: str = ""
    highlight_ranges: list[HighlightRange] = Field(default_factory=list)
    expected_output: list[str] = Field(default_factory=list)
    command: str = "java Main"
    stdout: list[str] = Field(default_factory=list)
    stderr: str = ""
    success: bool = True
    kind: QuizKind = QuizKind.predict_output
    question: str = "What will this print?"
    options: list[str] = Field(default_factory=list)
    answer: int = 0
    explanation: str = ""
    bullets: list[str] = Field(default_factory=list)
    takeaways: list[str] = Field(default_factory=list)
    concept_id: str = "for_loop"


class LessonDraft(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=160)
    language: str = Field(min_length=1, max_length=32)
    level: LessonLevel = LessonLevel.beginner
    topic: str = Field(min_length=1, max_length=200)
    objectives: list[str] = Field(min_length=1, max_length=8)
    concepts: list[str] = Field(default_factory=list)
    scenes: list[GenericScene] = Field(min_length=3, max_length=24)


def lesson_from_draft(draft: LessonDraft) -> Lesson:
    return Lesson.model_validate(draft.model_dump(mode="json"))


class ChatReply(BaseModel):
    reply: str = Field(min_length=1, max_length=4000)
    expression: TutorExpression = TutorExpression.explaining
    mini_visualization: VisualSpec | None = None
    should_execute: bool = False
    code: str | None = None
    language: str | None = None


class EvaluationResult(BaseModel):
    status: Literal["correct", "partially_correct", "incorrect"]
    misconception: str | None = None
    explanation: str
    next_action: Literal["continue", "reteach", "harder", "practice"] = "continue"
    mastery_delta: float = 0.0


class ImagePrompt(BaseModel):
    prompt: str
    aspect_ratio: str = "16:9"
    style: str = "educational_flat"
    seed: int = 7
