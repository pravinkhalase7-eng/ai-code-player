import { Composition } from "remotion";
import { LessonComposition } from "./LessonComposition";
import { COMPOSITION_ID, compositionSize, FPS, totalFrames, type AspectRatio } from "./utils/timing";
import type { Lesson } from "../types/lesson";

const SAMPLE: Lesson = {
  lesson_id: "java-for-loop",
  title: "Java For Loop",
  language: "java",
  level: "beginner",
  topic: "for loop",
  objectives: ["initialization", "condition", "increment"],
  scenes: [
    { id: "s1", type: "intro", duration: 6, narration: "Let's learn the Java for loop." },
    {
      id: "s2",
      type: "code",
      duration: 10,
      narration: "Here is the example.",
      code: "public class Main {\n    public static void main(String[] args) {\n        for (int i = 0; i < 5; i++) {\n            System.out.println(i);\n        }\n    }\n}\n",
      highlight_ranges: [{ start_line: 3, end_line: 3, start_col: 0, label: "loop" }],
    },
    {
      id: "s3",
      type: "terminal",
      duration: 6,
      narration: "The sandbox prints 0 through 4.",
      command: "java Main",
      stdout: ["0", "1", "2", "3", "4"],
    },
    {
      id: "s4",
      type: "quiz",
      duration: 6,
      narration: "What will it print?",
      question: "What will this print?",
      options: ["0 1 2 3 4", "1 2 3 4 5"],
    },
    { id: "s5", type: "summary", duration: 5, narration: "Initialization, condition, body, increment.", takeaways: ["i starts at 0"] },
  ],
};

export const RemotionRoot = () => {
  const aspect: AspectRatio = "16:9";
  const size = compositionSize(aspect);
  return (
    <Composition
      id={COMPOSITION_ID}
      component={LessonComposition}
      durationInFrames={totalFrames(SAMPLE)}
      fps={FPS}
      width={size.width}
      height={size.height}
      defaultProps={{ lesson: SAMPLE }}
    />
  );
};
