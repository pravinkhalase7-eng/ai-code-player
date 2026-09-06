export type LessonFormat = "lesson" | "reel";
export type LessonLevel = "beginner" | "intermediate" | "advanced";
export type SceneType =
  | "intro"
  | "concept"
  | "code"
  | "execution"
  | "terminal"
  | "quiz"
  | "summary";
export type TutorExpression =
  | "idle"
  | "talking"
  | "thinking"
  | "happy"
  | "confused"
  | "pointing"
  | "explaining"
  | "celebrating"
  | "listening";

export type HighlightRange = {
  start_line: number;
  end_line: number;
  start_col: number;
  end_col?: number | null;
  label: string;
  color?: string;
};

export type NarrationSegment = {
  start: number;
  end: number;
  text: string;
  highlight?: string | null;
  expression?: TutorExpression;
  gesture?: string;
};

export type VariableSnapshot = { name: string; value: string; type?: string };

export type ExecutionStep = {
  index: number;
  label: string;
  description: string;
  line: number;
  condition?: string | null;
  condition_result?: boolean | null;
  output_line?: string | null;
  variables: VariableSnapshot[];
  stopped?: boolean;
};

export type HashMapPutStep = {
  code: string;
  key: string;
  value: string;
  hash_bits?: string;
  bucket: number;
  color?: string;
};

export type VisualSpec = {
  kind?: string;
  title?: string;
  callouts?: string[];
  particles?: boolean;
};

export type HashMapVisual = {
  kind: "hashmap";
  capacity?: number;
  init_code?: string;
  setup_lines?: string[];
  puts?: HashMapPutStep[];
  node_fields?: string[];
};

export type LessonScene = {
  id: string;
  type: SceneType;
  duration: number;
  narration: string;
  segments?: NarrationSegment[];
  expression?: TutorExpression;
  audio_url?: string | null;
  visual?: VisualSpec | null;
  language?: string;
  filename?: string;
  code?: string;
  highlight_ranges?: HighlightRange[];
  expected_output?: string[];
  iterations?: ExecutionStep[];
  command?: string;
  stdout?: string[];
  stderr?: string;
  success?: boolean;
  verified?: boolean;
  kind?: string;
  question?: string;
  options?: string[];
  answer?: number | string | null;
  explanation?: string;
  bullets?: string[];
  diagram_steps?: { title: string; detail?: string; example?: string }[];
  visual_diagram?: HashMapVisual | null;
  takeaways?: string[];
  starter_code?: string | null;
  tests?: string[];
};

export type Lesson = {
  lesson_id: string;
  title: string;
  language: string;
  spoken_language?: string;
  level: LessonLevel;
  format?: LessonFormat;
  topic: string;
  objectives: string[];
  concepts?: string[];
  scenes: LessonScene[];
  thumbnail_url?: string | null;
  thumbnail_custom?: boolean;
  reel_seconds?: number;
  requires_code?: boolean;
  reel_mode?: string | null;
};

export type LessonSummary = {
  lesson_id: string;
  title: string;
  language: string;
  spoken_language?: string;
  level: string;
  format?: LessonFormat;
  status: string;
  completion_percent: number;
  scene_index?: number;
  topic: string;
  thumbnail_url?: string | null;
  reel_seconds?: number;
  reel_mode?: string | null;
  requires_code?: boolean;
};

export type RunHelp = {
  issue: string;
  explanation: string;
  line: number | null;
  label: string;
  suggested_code: string | null;
};
