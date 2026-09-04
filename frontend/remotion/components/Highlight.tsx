import { interpolate, useCurrentFrame } from "remotion";

export function Highlight({ active }: { active: boolean }) {
  const frame = useCurrentFrame();
  const opacity = active ? interpolate(frame % 20, [0, 10, 20], [0.35, 0.7, 0.35]) : 0;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: `rgba(251,191,36,${opacity})`,
        borderRadius: 6,
      }}
    />
  );
}
