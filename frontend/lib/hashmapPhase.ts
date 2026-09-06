export type PhaseKind = "hash" | "index" | "put" | "collision" | "tree" | "other";

export function classifyStep(title: string, detail?: string, example?: string): PhaseKind {
  const blob = `${title || ""} ${detail || ""} ${example || ""}`.toLowerCase();

  if (/treeify|tree-ify|red-?\s*black|\btree\b/.test(blob)) return "tree";
  if (/collision|collide/.test(blob)) return "collision";
  if (/\bindex\b|bucket\s*calc|bucket\s*index|hash\s*&\s*\(n/.test(blob)) return "index";
  if (/entry|node|storage|\bput\b|put\s*\(/.test(blob)) return "put";
  if (/hashcode|hash\s*code|\.hashcode\b|\bhash\b/.test(blob)) return "hash";
  return "other";
}

export function boardStateFromSteps(
  steps: { title: string; detail?: string; example?: string }[],
  activeStep: number,
  putCount: number,
): {
  activePutIndex: number; // -1 none yet
  progressHint: number; // 0..1 suggested
  phaseKind: PhaseKind;
  phaseLabel: string;
  phaseExample: string;
} {
  if (!steps.length) {
    return {
      activePutIndex: -1,
      progressHint: 0,
      phaseKind: "other",
      phaseLabel: "",
      phaseExample: "",
    };
  }

  const safeActive = Math.max(0, Math.min(activeStep, steps.length - 1));
  let putStepsSeen = 0;
  let phaseKind: PhaseKind = "other";
  let phaseLabel = "";
  let phaseExample = "";

  for (let i = 0; i <= safeActive; i++) {
    const step = steps[i];
    if (!step) continue;
    const kind = classifyStep(step.title, step.detail, step.example);
    if (i === safeActive) {
      phaseKind = kind;
      phaseLabel = step.title || "";
      phaseExample = step.example || step.detail || "";
    }
    if (kind === "put" || kind === "collision") {
      putStepsSeen += 1;
    }
  }

  // 0-based put index from put/collision steps counted up to activeStep; -1 before first put
  let activePutIndex = putStepsSeen > 0 ? putStepsSeen - 1 : -1;

  // Collision demos need the colliding (usually last) put on the board
  if (phaseKind === "collision" && putCount > 0) {
    activePutIndex = Math.max(activePutIndex, putCount - 1);
  }
  if (putCount > 0 && activePutIndex >= putCount) {
    activePutIndex = putCount - 1;
  }

  let progressHint = 0;
  if (phaseKind === "hash") progressHint = 0.18;
  else if (phaseKind === "index") progressHint = 0.28;
  else if (phaseKind === "put") progressHint = 0.72;
  else if (phaseKind === "collision") progressHint = 0.88;
  else if (phaseKind === "tree") progressHint = 1;
  else if (activePutIndex >= 0) progressHint = 0.6;

  // Tree keeps last put fully placed (progress=1)
  if (phaseKind === "tree") {
    progressHint = 1;
    if (putCount > 0) activePutIndex = putCount - 1;
  }

  return { activePutIndex, progressHint, phaseKind, phaseLabel, phaseExample };
}
