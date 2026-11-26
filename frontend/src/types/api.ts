/** Mirrors backend `app/core/schemas.py`: every error response has this shape. */
export interface ApiErrorDetail {
  field: string;
  message: string;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details: ApiErrorDetail[] | null;
}

export interface ApiErrorResponse {
  error: ApiErrorBody;
}

/**
 * Money arrives from the API as an exact decimal string ("4499.00") so no
 * precision is lost. Format it for display; never do arithmetic on floats.
 */
export type MoneyString = string;

/** ISO-8601 timestamp in UTC, e.g. "2026-11-25T14:12:38.321368Z". */
export type IsoDateTime = string;
