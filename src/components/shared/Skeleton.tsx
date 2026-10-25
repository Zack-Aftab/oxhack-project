export function Skeleton({ height = 56, className = "" }: { height?: number; className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-[16px] ${className}`}
      style={{ height, background: "var(--dot-off)" }}
    />
  );
}
