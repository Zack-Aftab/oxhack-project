export function SyntheticNotice({ notice, className = "" }: { notice: string; className?: string }) {
  return (
    <p className={`text-[12px] font-medium leading-4 text-muted-2 ${className}`} role="note">
      {notice}
    </p>
  );
}
