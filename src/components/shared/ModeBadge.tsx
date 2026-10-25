import type { DataMode } from "@/lib/api/mode";

export function ModeBadge({ mode }: { mode: DataMode }) {
  const live = mode === "live";
  return (
    <span
      className="inline-flex h-7 items-center gap-1.5 rounded-full px-2.5 text-[11.5px] font-semibold"
      style={{
        background: live ? "rgba(var(--accent-rgb), .1)" : "var(--surface)",
        border: live ? "1px solid transparent" : "1px dashed var(--hairline-2)",
        color: live ? "var(--accent)" : "var(--muted)",
      }}
      title={live ? "Calling same-origin /api routes" : "Serving committed fixtures; no backend involved"}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: live ? "var(--accent)" : "var(--chevron)" }} />
      {live ? "Live API" : "Sample data"}
    </span>
  );
}
