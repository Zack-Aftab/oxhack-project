import type { MultiCompareRequest, MultiCompareResponse } from "@contracts/multi-compare";
import type {
  CapacityRequest,
  CatalogResponse,
  CompareRequest,
  CompareResponse,
  DashboardResponse,
} from "@contracts/queuecare";
import type { DataMode } from "./mode";
import { getDataMode } from "./mode";
import type {
  ClassifyInput,
  ClassifyResponse,
  DestinationIntention,
  DestinationIntentionInput,
} from "./proposed";

/**
 * The one typed client both frontends use. Components never fetch or import fixtures directly.
 * The four core methods follow docs/INTERFACES.md; classify and intentions are proposals.
 */
export interface ApiClient {
  readonly mode: DataMode;
  getCatalog(): Promise<CatalogResponse>;
  compare(request: CompareRequest): Promise<CompareResponse>;
  /** Opt-in specialist/urgency contract; legacy single-category comparison is unchanged. */
  compareMultiple(request: MultiCompareRequest): Promise<MultiCompareResponse>;
  getDashboard(scenarioId: string, simulationAt: string): Promise<DashboardResponse>;
  updateCapacity(scenarioId: string, hospitalId: string, request: CapacityRequest): Promise<DashboardResponse>;
  /** Proposed POST /api/classify. */
  classify(input: ClassifyInput): Promise<ClassifyResponse>;
  /** Proposed POST /api/scenarios/{scenarioId}/events (destination_selected). */
  recordIntention(scenarioId: string, input: DestinationIntentionInput): Promise<DestinationIntention>;
  /** Proposed read of incoming intentions for the hospital screen. */
  listIntentions(scenarioId: string): Promise<DestinationIntention[]>;
}

let cached: ApiClient | null = null;

export async function getApiClient(): Promise<ApiClient> {
  if (cached) return cached;
  const mode = getDataMode();
  if (mode === "live") {
    const { createLiveClient } = await import("./live");
    cached = createLiveClient();
  } else {
    const { createSampleClient } = await import("./sample");
    cached = createSampleClient();
  }
  return cached;
}
