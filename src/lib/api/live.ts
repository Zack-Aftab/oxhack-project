import type {
  CapacityRequest,
  CatalogResponse,
  CompareResponse,
  DashboardResponse,
} from "@contracts/queuecare";
import type { ApiClient } from "./client";
import { ApiError, isErrorResponse } from "./errors";
import type { ClassifyInput, ClassifyResponse, DestinationIntention, DestinationIntentionInput } from "./proposed";

/** Same-origin Route Handlers. Paths follow docs/INTERFACES.md; classify/events are proposals. */
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { ...init, headers: { accept: "application/json", ...(init?.headers ?? {}) } });
  } catch (error) {
    throw new ApiError("NETWORK_ERROR", `Could not reach ${path}: ${(error as Error).message}`);
  }
  const text = await response.text();
  let body: unknown = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = null;
  }
  if (!response.ok) {
    if (isErrorResponse(body)) {
      throw new ApiError(body.error.code, body.error.message, response.status, body.error.currentStateVersion);
    }
    if (response.status === 404) {
      throw new ApiError("NOT_CONNECTED", `${path} is not implemented yet (HTTP 404).`, 404);
    }
    throw new ApiError("INTERNAL_ERROR", `${path} failed with HTTP ${response.status}.`, response.status);
  }
  return body as T;
}

const json = (value: unknown): RequestInit => ({
  headers: { "content-type": "application/json" },
  body: JSON.stringify(value),
});

export function createLiveClient(): ApiClient {
  return {
    mode: "live",
    getCatalog: () => request<CatalogResponse>("/api/catalog"),
    compare: (body) => request<CompareResponse>("/api/compare", { method: "POST", ...json(body) }),
    getDashboard: (scenarioId, simulationAt) => {
      const query = new URLSearchParams({ simulationAt });
      return request<DashboardResponse>(`/api/scenarios/${encodeURIComponent(scenarioId)}/dashboard?${query}`);
    },
    updateCapacity: (scenarioId, hospitalId, body: CapacityRequest) =>
      request<DashboardResponse>(
        `/api/scenarios/${encodeURIComponent(scenarioId)}/hospitals/${encodeURIComponent(hospitalId)}/capacity`,
        { method: "PATCH", ...json(body) },
      ),
    classify: async (input: ClassifyInput) => {
      const form = new FormData();
      if (input.description) form.set("symptoms", input.description);
      if (input.image) form.set("image", input.image);
      return request<ClassifyResponse>("/api/classify", { method: "POST", body: form });
    },
    recordIntention: (scenarioId, input: DestinationIntentionInput) =>
      request<DestinationIntention>(`/api/scenarios/${encodeURIComponent(scenarioId)}/events`, {
        method: "POST",
        ...json({ kind: "destination_selected", ...input }),
      }),
    listIntentions: (scenarioId) =>
      request<DestinationIntention[]>(`/api/scenarios/${encodeURIComponent(scenarioId)}/intentions`),
  };
}
