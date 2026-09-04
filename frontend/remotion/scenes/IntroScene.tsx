import { Caption, Stage } from "../components/Caption";
import { TutorAvatar } from "../components/TutorAvatar";
import type { LessonScene } from "../../types/lesson";

export function IntroScene({ scene }: { scene: LessonScene }) {
  return (
    <Stage>
      <TutorAvatar speaking />
      <h1 style={{ fontSize: 64, marginTop: 32 }}>{scene.narration}</h1>
      <Caption text={scene.narration} />
    </Stage>
  );
}
