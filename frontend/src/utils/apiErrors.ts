import { ApiError } from "@/lib/api/apiClient";

const UNKNOWN_ERROR_MESSAGE = "Something went wrong. Please try again.";

/** The user-facing message for any thrown value. Backend messages are already written for staff. */
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return UNKNOWN_ERROR_MESSAGE;
}

/** Per-field messages from a 404/409/422 response, e.g. which cart lines are short. */
export function getErrorDetails(error: unknown): ApiError["details"] {
  return error instanceof ApiError ? error.details : [];
}
