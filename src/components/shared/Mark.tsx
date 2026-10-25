/** Placeholder app mark from the design: ink square, white plus, blue dot. The product is unnamed. */
export function Mark({ size = 30 }: { size?: number }) {
  return (
    <span
      aria-hidden="true"
      style={{
        position: "relative",
        width: size,
        height: size,
        borderRadius: 10,
        background: "var(--ink)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        flex: "none",
      }}
    >
      <svg width={size * 0.53} height={size * 0.53} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round">
        <path d="M12 5v14M5 12h14" />
      </svg>
      <span
        style={{
          position: "absolute",
          right: -3,
          top: -3,
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: "var(--accent)",
          border: "2px solid var(--ground)",
        }}
      />
    </span>
  );
}
