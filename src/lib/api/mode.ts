export type DataMode = "sample" | "live";

/**
 * Explicit data mode, fixed at build time from NEXT_PUBLIC_DATA_MODE.
 * Sample mode serves committed fixtures; live mode calls same-origin Route Handlers.
 * A failed live request is shown as an error and is never replaced with a sample.
 */
export function getDataMode(): DataMode {
  return process.env.NEXT_PUBLIC_DATA_MODE === "live" ? "live" : "sample";
}
