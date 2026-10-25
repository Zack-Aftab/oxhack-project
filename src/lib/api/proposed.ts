/**
 * PROPOSED extensions, not part of contracts/queuecare.ts yet.
 * See docs/build/MODELS-AND-DATA.md#backend-changes-to-agree. Promote into the shared
 * contract (docs + types + fixtures together) only after the backend owner agrees.
 */
import type { ComplaintCategory } from "@contracts/queuecare";

export interface ClassifyInput {
  description: string;
  image: File | null;
}

export interface ClassifyResponse {
  /** Exact catalog ID, or null when no suggestion is available. */
  suggestedCategory: ComplaintCategory | null;
  requiresConfirmation: true;
  /** Who produced the suggestion. "none" means the user must choose manually. */
  source: "gemini" | "none";
  message?: string;
}

export interface DestinationIntentionInput {
  hospitalId: string;
  complaintCategory: ComplaintCategory;
  simulationAt: string;
  estimatedArrivalAt: string | null;
  expectedStateVersion: number;
}

export interface DestinationIntention extends DestinationIntentionInput {
  intentionId: string;
  scenarioId: string;
  recordedAt: string;
  /** Where the record lives. Sample mode keeps it in this browser tab only. */
  storage: "sample_tab" | "backend";
}
