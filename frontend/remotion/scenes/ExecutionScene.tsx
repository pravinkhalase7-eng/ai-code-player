import { interpolate, useCurrentFrame } from "remotion";
import { Caption, Stage } from "../components/Caption";
import { CodeEditor } from "../components/CodeEditor";
import { VariablePanel } from "../components/VariablePanel";
import type { LessonScene } from "../../types/lesson";

export function ExecutionScene({ scene }: { scene: LessonScene }) {
  const frame = useCurrentFrame();
  const steps = scene.iterations ?? [];
  const index = steps.length
    ? Math.min(
        steps.length - 1,
        Math.max(
          0,
          Math.floor(
            interpolate(frame, [0, Math.max(1, steps.length) * 18], [0, steps.length], {
              extrapolateRight: "clamp",
            }),
          ),
        ),
      )
    : 0;
  const step = steps[index];
  return (
    <Stage>
      <div style={{ display: "flex", gap: 24, height: "100%" }}>
        <CodeEditor code={scene.code || ""} highlightLine={step?.line} />
        <div>
          <h2>{step?.label || "STEP"}</h2>
          <p style={{ fontSize: 28 }}>{step?.description}</p>
          <VariablePanel name={step?.variables[0]?.name || "i"} value={step?.variables[0]?.value || "0"} />
        </div>
      </div>
      <Caption text={step?.description || scene.narration} />
    </Stage>
  );
}
