"use client";

import Link from "next/link";
import { getApiClient } from "@/lib/api/client";
import { getDataMode } from "@/lib/api/mode";
import { useResource } from "@/lib/useResource";
import { formatClock, formatDate } from "@/lib/format";
import { ErrorCard } from "@/components/shared/ErrorCard";
import { Mark } from "@/components/shared/Mark";
import { ModeBadge } from "@/components/shared/ModeBadge";
import { Skeleton } from "@/components/shared/Skeleton";
import { SyntheticNotice } from "@/components/shared/SyntheticNotice";

/**
 * Foundation shell: proves the typed client end to end by loading the catalog.
 * The patient journey (describe → confirm → results → selected) replaces this on the UI branch.
 */
export function PatientShell() {
  const { data: catalog, error, loading, reload } = useResource(
    async () => (await getApiClient()).getCatalog(),
    "catalog",
  );

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[430px] flex-col px-5 pb-10 pt-[58px]">
      <header className="flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-ink no-underline">
          <Mark />
          <span className="text-[15px] font-bold tracking-[-0.02em]">Demo</span>
        </Link>
        <ModeBadge mode={getDataMode()} />
      </header>

      <h1 className="pop mt-10 text-[40px] font-bold leading-[44px] tracking-[-0.035em]">
        <span className="text-muted-2">Tell us</span>
        <br />
        what happened.
      </h1>
      <p className="mt-3 text-muted">Patient screens are being built on the UI branch. This shell shows the catalog the client returns.</p>

      <section className="mt-6 flex flex-col gap-3">
        {loading ? (
          <>
            <Skeleton height={48} />
            <Skeleton height={160} />
          </>
        ) : error ? (
          <ErrorCard error={error} onRetry={reload} />
        ) : catalog ? (
          <>
            <div className="glass pop rounded-[22px] p-4">
              <div className="eyebrow">Scenario</div>
              <div className="mt-1 text-[16px] font-semibold">
                {catalog.defaultComparison.scenarioId} · {formatDate(catalog.defaultComparison.simulationAt)} ·{" "}
                <span className="num">{formatClock(catalog.defaultComparison.simulationAt)}</span>
              </div>
              <div className="mt-1 text-[12.5px] text-muted">{catalog.demoOrigin.label}</div>
            </div>
            <div className="glass pop rounded-[22px] p-4" style={{ animationDelay: ".06s" }}>
              <div className="eyebrow">Complaint categories</div>
              <ul className="mt-2 flex flex-wrap gap-1.5">
                {catalog.complaintCategories.map((category) => (
                  <li
                    key={category.id}
                    className="inline-flex h-[30px] items-center rounded-full border border-[var(--hairline)] bg-[var(--surface)] px-3 text-[13px] font-semibold"
                    title={category.id}
                  >
                    {category.label}
                  </li>
                ))}
              </ul>
            </div>
            <div className="glass pop rounded-[22px] p-4" style={{ animationDelay: ".12s" }}>
              <div className="eyebrow">Hospitals</div>
              <ul className="mt-2 flex flex-col gap-1 text-[14px] font-medium">
                {catalog.hospitals.map((h) => (
                  <li key={h.hospitalId} className="flex justify-between gap-3">
                    <span>{h.name}</span>
                    <span className="num text-muted-2">{h.hospitalId}</span>
                  </li>
                ))}
              </ul>
            </div>
            <SyntheticNotice notice={catalog.notice} className="mt-2" />
          </>
        ) : null}
      </section>

      <div className="mt-auto flex items-center justify-center gap-2 pt-8 text-[12.5px] font-medium text-muted">
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--emergency)]" />
        <span>
          Emergency?{" "}
          <a href="tel:999" className="font-bold text-ink no-underline">
            Call 999
          </a>
          . Unsure?{" "}
          <a href="tel:111" className="font-bold text-ink no-underline">
            NHS 111
          </a>
          .
        </span>
      </div>
    </main>
  );
}
