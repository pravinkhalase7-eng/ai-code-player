import { interpolate, useCurrentFrame } from "remotion";

export function CodeEditor({
  code,
  highlightLine,
  filename = "Main.java",
}: {
  code: string;
  highlightLine?: number;
  filename?: string;
}) {
  const frame = useCurrentFrame();
  const chars = Math.max(1, Math.floor(interpolate(frame, [0, 40], [0, code.length], { extrapolateRight: "clamp" })));
  const visible = code.slice(0, chars);
  const lines = visible.split("\n");
  return (
    <div
      style={{
        flex: 1,
        background: "#0b1220",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: 24,
        overflow: "hidden",
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
      }}
    >
      <div style={{ padding: "12px 18px", borderBottom: "1px solid rgba(255,255,255,0.08)", color: "#e4e4e7" }}>
        {filename}
      </div>
      <div style={{ padding: 18, fontSize: 22, lineHeight: 1.45, color: "#f4f4f5" }}>
        {lines.map((line, index) => (
          <div
            key={`${line}-${index}`}
            style={{
              background: highlightLine === index + 1 ? "rgba(251,191,36,0.18)" : "transparent",
              borderRadius: 6,
              padding: "0 8px",
            }}
          >
            <span style={{ color: "#64748b", marginRight: 16 }}>
              {String(index + 1).padStart(2, "0")}
            </span>
            {line || " "}
            {index === lines.length - 1 ? <span style={{ color: "#fbbf24" }}>|</span> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
