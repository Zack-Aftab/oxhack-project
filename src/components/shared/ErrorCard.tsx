"use client";

import { ApiError } from "@/lib/api/errors";

const TITLES: Partial<Record<ApiError["code"], string>> = {
  NETWORK_ERROR: "Couldn't reach the server",
  NOT_CONNECTED: "This route isn't connected yet",
  SAMPLE_UNAVAILABLE: "No sample for this request",
  STATE_CONFLICT: "Someone else changed this scenario",
  SIMULATION_TIME_UNAVAILABLE: "No data for this time",
  INVALID_REQUEST: "The request was rejected",
  UNKNOWN_RESOURCE: "Not found",
  INTERNAL_ERROR: "Something went wrong",
};

export function ErrorCard({
  error,
  onRetry,
  retryLabel = "Retry",
}: {
  error: unknown;
  onRetry?: () => void;
  retryLabel?: string;
}) {
  const apiError = ApiError.from(error);
  return (
    <div className="dashed pop p-4" role="alert">
      <div className="text-[14px] font-semibold text-ink">{TITLES[apiError.code] ?? "Request failed"}</div>
      <p className="mt-1 text-[12.5px] leading-[17px]">{apiError.message}</p>
      <p className="mt-1 text-[11px] text-muted-2">
        {apiError.code}
        {apiError.status ? ` · HTTP ${apiError.status}` : ""}
        {apiError.currentStateVersion !== undefined ? ` · current version ${apiError.currentStateVersion}` : ""}
      </p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 inline-flex h-9 items-center rounded-full border border-[var(--hairline)] bg-[var(--surface)] px-4 text-[13px] font-semibold text-ink"
        >
          {retryLabel}
        </button>
      ) : null}
    </div>
  );
}
