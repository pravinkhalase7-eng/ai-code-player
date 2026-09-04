import { Caption, Stage } from "../components/Caption";
import type { LessonScene } from "../../types/lesson";

export function SummaryScene({ scene }: { scene: LessonScene }) {
  return (
    <Stage>
      <h1 style={{ fontSize: 56 }}>You learned it.</h1>
      {(scene.takeaways ?? []).map((item) => (
        <p key={item} style={{ fontSize: 32, color: "#fde68a" }}>
          {item}
        </p>
      ))}
      <Caption text={scene.narration} />
    </Stage>
  );
}
