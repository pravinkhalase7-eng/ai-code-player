import { Caption, Stage } from "../components/Caption";
import { Terminal } from "../components/Terminal";
import type { LessonScene } from "../../types/lesson";

export function TerminalScene({ scene }: { scene: LessonScene }) {
  return (
    <Stage>
      <h1 style={{ fontSize: 42, marginBottom: 24 }}>Real sandbox output</h1>
      <Terminal command={scene.command || "java Main"} lines={scene.stdout || []} />
      <Caption text={scene.narration} />
    </Stage>
  );
}
