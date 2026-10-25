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
 * Foundation shell: loads the dashboard for the default scenario through the typed client.
 * The five-tab dashboard ported from the HTML prototype replaces this on the UI branch.
 */
export function HospitalShell() {
  const { data, error, loading, reload } = useResource(async () => {
    const client = await getApiClient();
    const catalog = await client.getCatalog();
    const { scenarioId, simulationAt } = catalog.defaultComparison;
    const dashboard = await client.getDashboard(scenarioId, simulationAt);
    return { catalog, dashboard };
  }, "dashboard");

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-6 px-8 pb-10 pt-6">
      <header className="glass flex h-16 items-center justify-between rounded-[22px] px-5">
        <Link href="/" className="flex items-center gap-2.5 text-ink no-underline">
          <Mark />
          <span className="text-[15px] font-bold tracking-[-0.02em]">
            Demo <span className="text-[11.5px] font-medium text-muted-2">Hospital operations</span>
          </span>
        </Link>
        <div className="flex items-center gap-3 text-[13px] font-semibold text-ink-2">
          {data ? (
            <span className="num">
              <span className="text-muted">{formatDate(data.dashboard.simulationAt)}</span> ·{" "}
              {formatClock(data.dashboard.simulationAt)} · scenario {data.dashboard.scenarioId} v{data.dashboard.stateVersion}
            </span>
          ) : null}
          <ModeBadge mode={getDataMode()} />
        </div>
      </header>

      <div>
        <div className="eyebrow">Emergency department / Operations</div>
        <h1 className="mt-2 text-[34px] font-bold leading-[38px] tracking-[-0.035em]">
          <span className="text-muted-2">Overview</span> shell.
        </h1>
        <p className="mt-1.5 max-w-[65ch] text-muted">
          The five-tab dashboard is being ported on the UI branch. This shell shows the scenario the client returns.
        </p>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-5">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} height={140} />
          ))}
        </div>
      ) : error ? (
        <ErrorCard error={error} onRetry={reload} />
      ) : data ? (
        <>
          <div className="grid gap-4 md:grid-cols-5">
            {data.dashboard.hospitals.map((h, i) => (
              <section
                key={h.hospitalId}
                className="pop flex flex-col gap-2 rounded-[22px] border border-[var(--hairline)] bg-[var(--surface)] p-4"
                style={{ animationDelay: `${i * 0.06}s`, boxShadow: "var(--shadow-white-inset)" }}
              >
                <div className="eyebrow">{h.hospitalId}</div>
                <div className="text-[15px] font-semibold leading-5">{h.name}</div>
                <dl className="num mt-1 grid grid-cols-[1fr_auto] gap-x-3 gap-y-1 text-[12.5px]">
                  <dt className="text-muted">Waiting for referral</dt>
                  <dd className="font-semibold">{h.waitingForReferral}</dd>
                  <dt className="text-muted">Waiting for diagnosis</dt>
                  <dd className="font-semibold">{h.waitingForDiagnosis}</dd>
                  <dt className="text-muted">General doctors</dt>
                  <dd className="font-semibold">
                    {h.generalDoctorsAvailable}
                    {h.generalDoctorsAvailable !== h.baselineGeneralDoctorsAvailable ? (
                      <span className="text-muted-2"> (source {h.baselineGeneralDoctorsAvailable})</span>
                    ) : null}
                  </dd>
                  <dt className="text-muted">ED spaces</dt>
                  <dd className="font-semibold">{h.bedsAvailable}</dd>
                  <dt className="text-muted">Historical arrivals in window</dt>
                  <dd className="font-semibold">{h.historicalArrivalsInWindow}</dd>
                </dl>
                <div className="text-[11px] text-muted-2">
                  {formatClock(h.windowStart)}–{formatClock(h.windowEnd)} · {h.snapshotId}
                </div>
              </section>
            ))}
          </div>
          <SyntheticNotice notice={data.dashboard.notice} />
        </>
      ) : null}
    </main>
  );
}
