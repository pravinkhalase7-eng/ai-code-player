import { Sequence } from "remotion";
import type { Lesson } from "../types/lesson";
import { CodeScene } from "./scenes/CodeScene";
import { ConceptScene } from "./scenes/ConceptScene";
import { ExecutionScene } from "./scenes/ExecutionScene";
import { IntroScene } from "./scenes/IntroScene";
import { QuizScene } from "./scenes/QuizScene";
import { SummaryScene } from "./scenes/SummaryScene";
import { TerminalScene } from "./scenes/TerminalScene";
import { sceneFrames } from "./utils/timing";

export function LessonComposition({ lesson }: { lesson: Lesson }) {
  let from = 0;
  return (
    <>
      {lesson.scenes.map((scene) => {
        const durationInFrames = sceneFrames(scene.duration);
        const start = from;
        from += durationInFrames;
        const body =
          scene.type === "intro" ? (
            <IntroScene scene={scene} />
          ) : scene.type === "concept" ? (
            <ConceptScene scene={scene} />
          ) : scene.type === "code" ? (
            <CodeScene scene={scene} />
          ) : scene.type === "execution" ? (
            <ExecutionScene scene={scene} />
          ) : scene.type === "terminal" ? (
            <TerminalScene scene={scene} />
          ) : scene.type === "quiz" ? (
            <QuizScene scene={scene} />
          ) : (
            <SummaryScene scene={scene} />
          );
        return (
          <Sequence key={scene.id} from={start} durationInFrames={durationInFrames}>
            {body}
          </Sequence>
        );
      })}
    </>
  );
}
