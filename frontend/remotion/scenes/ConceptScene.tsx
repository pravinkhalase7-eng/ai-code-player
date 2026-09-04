import { Caption, Stage } from "../components/Caption";
import { TutorAvatar } from "../components/TutorAvatar";
import type { LessonScene } from "../../types/lesson";

export function ConceptScene({ scene }: { scene: LessonScene }) {
  return (
    <Stage>
      <div style={{ display: "flex", gap: 40 }}>
        <TutorAvatar speaking />
        <div>
          <h1 style={{ fontSize: 48 }}>The idea</h1>
          {(scene.bullets ?? []).map((item) => (
            <p key={item} style={{ fontSize: 32, color: "#fde68a" }}>
              {item}
            </p>
          ))}
        </div>
      </div>
      <Caption text={scene.narration} />
    </Stage>
  );
}
