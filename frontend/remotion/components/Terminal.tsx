import { interpolate, useCurrentFrame } from "remotion";

export function Terminal({ command, lines }: { command: string; lines: string[] }) {
  const frame = useCurrentFrame();
  const shown = Math.max(0, Math.floor(interpolate(frame, [10, 10 + lines.length * 8], [0, lines.length], { extrapolateRight: "clamp" })));
  return (
    <div
      style={{
        background: "#09090b",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: 18,
        padding: 18,
        fontFamily: "ui-monospace, Menlo, monospace",
        color: "#e4e4e7",
        minHeight: 160,
      }}
    >
      <div style={{ color: "#fde68a", marginBottom: 8 }}>$ {command}</div>
      {lines.slice(0, shown).map((line) => (
        <div key={line}>
          <span style={{ color: "#71717a" }}>&gt; </span>
          {line}
        </div>
      ))}
    </div>
  );
}
