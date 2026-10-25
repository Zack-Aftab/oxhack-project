import type {
  CapacityRequest,
  CatalogResponse,
  CompareRequest,
  CompareResponse,
  DashboardResponse,
} from "@contracts/queuecare";
import catalogFixture from "@fixtures/queuecare/catalog.response.json";
import compareBaseline from "@fixtures/queuecare/compare.response.json";
import compareChanged from "@fixtures/queuecare/compare.capacity-changed.response.json";
import compareNoTravel from "@fixtures/queuecare/compare.no-travel.response.json";
import compareUnknown from "@fixtures/queuecare/compare.unknown-category.response.json";
import compareNoDoctors from "@fixtures/queuecare/compare.no-general-doctors.response.json";
import dashboardBaseline from "@fixtures/queuecare/dashboard.response.json";
import dashboardChanged from "@fixtures/queuecare/dashboard.capacity-changed.response.json";
import type { ApiClient } from "./client";
import { ApiError } from "./errors";
import type { ClassifyInput, DestinationIntention, DestinationIntentionInput } from "./proposed";

/**
 * Sample adapter: the committed fixtures plus one in-memory scenario per browser tab.
 * It mimics the contract's status codes so every UI state can be exercised offline.
 * It is not a backend and cannot show another browser's changes.
 */
const catalog = catalogFixture as unknown as CatalogResponse;
const fixtures = {
  compareBaseline: compareBaseline as unknown as CompareResponse,
  compareChanged: compareChanged as unknown as CompareResponse,
  compareNoTravel: compareNoTravel as unknown as CompareResponse,
  compareUnknown: compareUnknown as unknown as CompareResponse,
  compareNoDoctors: compareNoDoctors as unknown as CompareResponse,
  dashboardBaseline: dashboardBaseline as unknown as DashboardResponse,
  dashboardChanged: dashboardChanged as unknown as DashboardResponse,
};

/** Which H001 general-doctor count the scenario currently holds; only these have fixtures. */
type Variant = "baseline" | "h001-8" | "h001-0";

interface SampleScenario {
  stateVersion: number;
  variant: Variant;
  intentions: DestinationIntention[];
}

const SCENARIO_ID = catalog.defaultComparison.scenarioId;
const SIMULATION_AT = catalog.defaultComparison.simulationAt;
const FIXTURE_CATEGORY = catalog.defaultComparison.complaintCategory;
const CAPACITY_HOSPITAL = "H001";

const scenario: SampleScenario = { stateVersion: 0, variant: "baseline", intentions: [] };

const latency = () => new Promise((resolve) => setTimeout(resolve, 350));
const clone = <T>(value: T): T => structuredClone(value);

function assertScenario(scenarioId: string) {
  if (scenarioId !== SCENARIO_ID) {
    throw new ApiError("UNKNOWN_RESOURCE", `Unknown scenario "${scenarioId}". Sample mode only has "${SCENARIO_ID}".`, 404);
  }
}

function assertClock(simulationAt: string) {
  if (simulationAt !== SIMULATION_AT) {
    throw new ApiError(
      "SIMULATION_TIME_UNAVAILABLE",
      `Sample mode only has fixtures for ${SIMULATION_AT}; requested ${simulationAt}.`,
      422,
    );
  }
}

function withVersion<T extends { stateVersion: number }>(value: T): T {
  const copy = clone(value);
  copy.stateVersion = scenario.stateVersion;
  return copy;
}

function currentDashboard(): DashboardResponse {
  if (scenario.variant === "baseline") return withVersion(fixtures.dashboardBaseline);
  if (scenario.variant === "h001-8") return withVersion(fixtures.dashboardChanged);
  // Zero general doctors: same source snapshot, only the scenario override differs.
  const dashboard = withVersion(fixtures.dashboardBaseline);
  const h001 = dashboard.hospitals.find((h) => h.hospitalId === CAPACITY_HOSPITAL);
  if (h001) h001.generalDoctorsAvailable = 0;
  return dashboard;
}

export function createSampleClient(): ApiClient {
  return {
    mode: "sample",

    async getCatalog() {
      await latency();
      return clone(catalog);
    },

    async compare(request: CompareRequest) {
      await latency();
      assertScenario(request.scenarioId);
      assertClock(request.simulationAt);
      if (request.originId !== "london-demo") {
        throw new ApiError("INVALID_REQUEST", `originId must be "london-demo" for demo travel.`, 422);
      }
      if (!catalog.complaintCategories.some((c) => c.id === request.complaintCategory)) {
        throw new ApiError("INVALID_REQUEST", "complaintCategory must be a catalog ID", 422);
      }
      if (request.complaintCategory === "unknown") return withVersion(fixtures.compareUnknown);
      if (request.complaintCategory !== FIXTURE_CATEGORY) {
        throw new ApiError(
          "SAMPLE_UNAVAILABLE",
          `Sample mode only has a comparison fixture for "${FIXTURE_CATEGORY}". Choose that category, or connect the backend for other categories.`,
          501,
        );
      }
      if (request.travelMode === "unavailable") return withVersion(fixtures.compareNoTravel);
      if (scenario.variant === "h001-8") return withVersion(fixtures.compareChanged);
      if (scenario.variant === "h001-0") return withVersion(fixtures.compareNoDoctors);
      return withVersion(fixtures.compareBaseline);
    },

    async getDashboard(scenarioId, simulationAt) {
      await latency();
      assertScenario(scenarioId);
      assertClock(simulationAt);
      return currentDashboard();
    },

    async updateCapacity(scenarioId, hospitalId, request: CapacityRequest) {
      await latency();
      assertScenario(scenarioId);
      assertClock(request.simulationAt);
      if (!catalog.hospitals.some((h) => h.hospitalId === hospitalId)) {
        throw new ApiError("UNKNOWN_RESOURCE", `Unknown hospital "${hospitalId}".`, 404);
      }
      if (!Number.isInteger(request.generalDoctorsAvailable) || request.generalDoctorsAvailable < 0) {
        throw new ApiError("INVALID_REQUEST", "generalDoctorsAvailable must be a nonnegative integer.", 422);
      }
      if (request.expectedStateVersion !== scenario.stateVersion) {
        throw new ApiError(
          "STATE_CONFLICT",
          `Scenario is at version ${scenario.stateVersion}, not ${request.expectedStateVersion}. Refresh before retrying.`,
          409,
          scenario.stateVersion,
        );
      }
      const variants: Record<number, Variant> = { 16: "baseline", 8: "h001-8", 0: "h001-0" };
      const next = hospitalId === CAPACITY_HOSPITAL ? variants[request.generalDoctorsAvailable] : undefined;
      if (!next) {
        throw new ApiError(
          "SAMPLE_UNAVAILABLE",
          `Sample mode only has fixtures for ${CAPACITY_HOSPITAL} at 16, 8 or 0 general doctors in this window. Other changes need the backend.`,
          501,
        );
      }
      scenario.variant = next;
      scenario.stateVersion += 1;
      return currentDashboard();
    },

    async classify(input: ClassifyInput) {
      await latency();
      const what = [input.description && "description", input.image && "photo"].filter(Boolean).join(" and ");
      return {
        suggestedCategory: null,
        requiresConfirmation: true,
        source: "none",
        message: what
          ? `No classifier is connected in sample mode, so your ${what} was not analysed. Choose the category yourself.`
          : "Add a description or photo, or choose the category yourself.",
      };
    },

    async recordIntention(scenarioId, input: DestinationIntentionInput) {
      await latency();
      assertScenario(scenarioId);
      if (input.expectedStateVersion !== scenario.stateVersion) {
        throw new ApiError(
          "STATE_CONFLICT",
          `Scenario moved to version ${scenario.stateVersion}. Compare again before choosing.`,
          409,
          scenario.stateVersion,
        );
      }
      const intention: DestinationIntention = {
        ...input,
        intentionId: `sample-${scenario.intentions.length + 1}`,
        scenarioId,
        recordedAt: new Date().toISOString(),
        storage: "sample_tab",
      };
      scenario.intentions.push(intention);
      return clone(intention);
    },

    async listIntentions(scenarioId) {
      await latency();
      assertScenario(scenarioId);
      return clone(scenario.intentions);
    },
  };
}

/** Test/demo helper: restore the baseline fixtures in this tab. Sample mode only. */
export function resetSampleScenario() {
  scenario.stateVersion = 0;
  scenario.variant = "baseline";
  scenario.intentions = [];
}
