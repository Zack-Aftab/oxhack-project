import type { ErrorResponse } from "@contracts/queuecare";

export type ApiErrorCode =
  | ErrorResponse["error"]["code"]
  | "NETWORK_ERROR"
  | "SAMPLE_UNAVAILABLE"
  | "NOT_CONNECTED";

/** One error shape for both adapters so screens render the same retry state. */
export class ApiError extends Error {
  readonly code: ApiErrorCode;
  readonly status: number;
  readonly currentStateVersion?: number;

  constructor(code: ApiErrorCode, message: string, status = 0, currentStateVersion?: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.currentStateVersion = currentStateVersion;
  }

  static from(error: unknown): ApiError {
    if (error instanceof ApiError) return error;
    if (error instanceof Error) return new ApiError("NETWORK_ERROR", error.message);
    return new ApiError("NETWORK_ERROR", "Request failed");
  }
}

export function isErrorResponse(body: unknown): body is ErrorResponse {
  if (!body || typeof body !== "object") return false;
  const candidate = body as { error?: { code?: unknown; message?: unknown } };
  return typeof candidate.error?.code === "string" && typeof candidate.error?.message === "string";
}
