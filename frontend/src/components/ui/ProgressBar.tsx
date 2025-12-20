type Props = {
  value: number;
  label?: string;
};

export function ProgressBar({ value, label }: Props) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div>
      {label && (
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
          <span style={{ color: "var(--gray-300)" }}>{label}</span>
          <span style={{ color: "var(--gray-100)", fontWeight: 700 }}>{clamped}%</span>
        </div>
      )}
      <div
        style={{
          height: 12,
          background: "rgba(255,255,255,0.08)",
          borderRadius: 999,
          overflow: "hidden",
          border: "1px solid rgba(255,255,255,0.06)"
        }}
      >
        <div
          style={{
            width: `${clamped}%`,
            height: "100%",
            background: "linear-gradient(90deg, #0ea5e9, #22d3ee)",
            transition: "width 200ms ease"
          }}
        />
      </div>
    </div>
  );
}
