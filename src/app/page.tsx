import Link from "next/link";
import { getDataMode } from "@/lib/api/mode";
import { Mark } from "@/components/shared/Mark";
import { ModeBadge } from "@/components/shared/ModeBadge";

export default function IndexPage() {
  const mode = getDataMode();
  return (
    <main className="mx-auto flex min-h-screen max-w-[720px] flex-col gap-6 px-5 pb-16 pt-14">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Mark />
          <span className="text-[15px] font-bold tracking-[-0.02em]">Demo (unnamed)</span>
        </div>
        <ModeBadge mode={mode} />
      </header>

      <h1 className="text-[40px] font-bold leading-[44px] tracking-[-0.035em]">
        <span className="text-muted-2">One scenario,</span>
        <br />
        two screens.
      </h1>
      <p className="max-w-[60ch] text-muted">
        A patient compares five simulated London hospitals; a hospital user changes a staffing
        scenario and sees the same comparison move. Synthetic data only. Not clinical guidance.
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        <Link
          href="/patient"
          className="glass pop block rounded-[26px] p-5 text-ink no-underline transition hover:bg-[var(--glass-bg-hover)]"
        >
          <div className="eyebrow">Patient</div>
          <div className="mt-2 text-[19px] font-bold tracking-[-0.02em]">Where will I be seen soonest?</div>
          <p className="mt-1 text-[13px] text-muted">
            Describe what happened, confirm the category, compare hospitals, choose where to go.
          </p>
        </Link>
        <Link
          href="/hospital"
          className="glass pop block rounded-[26px] p-5 text-ink no-underline transition hover:bg-[var(--glass-bg-hover)]"
          style={{ animationDelay: ".06s" }}
        >
          <div className="eyebrow">Hospital</div>
          <div className="mt-2 text-[19px] font-bold tracking-[-0.02em]">Operations dashboard</div>
          <p className="mt-1 text-[13px] text-muted">
            Queues, staffing and a general-doctor scenario that changes the patient comparison.
          </p>
        </Link>
      </div>

      <footer className="mt-auto text-[12px] text-muted-2">
        Data mode is set with <code>NEXT_PUBLIC_DATA_MODE</code>. See docs/SETUP.md.
      </footer>
    </main>
  );
}
