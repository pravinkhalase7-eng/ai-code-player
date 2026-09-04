import { Caption, Stage } from "../components/Caption";
import type { LessonScene } from "../../types/lesson";

export function QuizScene({ scene }: { scene: LessonScene }) {
  return (
    <Stage>
      <h1 style={{ fontSize: 48 }}>{scene.question}</h1>
      {(scene.options ?? []).map((option, index) => (
        <div
          key={option}
          style={{
            marginTop: 16,
            padding: 18,
            borderRadius: 16,
            background: "rgba(255,255,255,0.06)",
            fontSize: 28,
          }}
        >
          {index + 1}. {option}
        </div>
      ))}
      <Caption text={scene.narration} />
    </Stage>
  );
}
