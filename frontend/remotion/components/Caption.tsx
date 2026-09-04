import type { ReactNode } from "react";
import { AbsoluteFill } from "remotion";

export function Caption({ text }: { text: string }) {
  return (
    <div
      style={{
        position: "absolute",
        bottom: 48,
        left: 48,
        right: 48,
        textAlign: "center",
        color: "white",
        fontSize: 28,
        background: "rgba(0,0,0,0.62)",
        padding: "16px 24px",
        borderRadius: 18,
      }}
    >
      {text}
    </div>
  );
}

export function Stage({ children }: { children: ReactNode }) {
  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg,#09090b 0%,#18181b 100%)",
        fontFamily: "Geist, ui-sans-serif, system-ui",
        color: "white",
        padding: 48,
      }}
    >
      {children}
    </AbsoluteFill>
  );
}
