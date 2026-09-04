import { interpolate, useCurrentFrame } from "remotion";
import { Caption, Stage } from "../components/Caption";
import { CodeEditor } from "../components/CodeEditor";
import type { LessonScene } from "../../types/lesson";

export function CodeScene({ scene }: { scene: LessonScene }) {
  const frame = useCurrentFrame();
  const ranges = scene.highlight_ranges ?? [];
  const active = ranges[Math.min(ranges.length - 1, Math.floor(interpolate(frame, [15, 90], [0, Math.max(1, ranges.length)], { extrapolateRight: "clamp" })))];
  return (
    <Stage>
      <CodeEditor code={scene.code || ""} highlightLine={active?.start_line} filename={scene.filename} />
      <Caption text={scene.narration} />
    </Stage>
  );
}
