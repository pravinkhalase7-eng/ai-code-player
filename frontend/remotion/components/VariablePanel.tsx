export function VariablePanel({ name, value }: { name: string; value: string }) {
  return (
    <div
      style={{
        border: "1px solid rgba(251,191,36,0.3)",
        background: "rgba(251,191,36,0.08)",
        borderRadius: 18,
        padding: 20,
        minWidth: 240,
      }}
    >
      <div style={{ fontSize: 14, letterSpacing: 3, textTransform: "uppercase", color: "#fde68a" }}>
        Variables
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 12, fontSize: 28 }}>
        <span>{name}</span>
        <span style={{ color: "#fbbf24" }}>{value}</span>
      </div>
    </div>
  );
}
