export function TutorAvatar({ speaking }: { speaking: boolean }) {
  return (
    <div style={{ width: 160, textAlign: "center" }}>
      <div
        style={{
          height: 120,
          width: 120,
          margin: "0 auto",
          borderRadius: "50%",
          background: "#fbbf24",
          transform: speaking ? "translateY(-4px)" : undefined,
          boxShadow: "0 18px 40px rgba(251,191,36,0.35)",
        }}
      />
      <div style={{ marginTop: 8, letterSpacing: 3, fontSize: 12, color: "#fde68a" }}>PAVI</div>
    </div>
  );
}
