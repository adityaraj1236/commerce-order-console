import type { ApiErrorBody, ApiErrorDetail } from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

const FALLBACK_ERROR_MESSAGE = "Something went wrong. Please try again.";
const NETWORK_ERROR_MESSAGE =
  "Cannot reach the server. Check that the backend is running and try again.";

/** Every failed request becomes an ApiError carrying the backend's code and message. */
export class ApiError extends Error {
  status: number;
  code: string;
  details: ApiErrorDetail[];

  constructor(status: number, code: string, message: string, details: ApiErrorDetail[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

type QueryValue = string | number | undefined;

interface ApiRequestOptions {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  query?: Record<string, QueryValue>;
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  }
  const queryString = params.toString();
  return `${API_BASE_URL}${path}${queryString ? `?${queryString}` : ""}`;
}

export async function apiRequest<TResponse>(
  path: string,
  { method = "GET", body, query }: ApiRequestOptions = {},
): Promise<TResponse> {
  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, "network_error", NETWORK_ERROR_MESSAGE);
  }

  const data: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const errorBody = (data as { error?: ApiErrorBody } | null)?.error;
    throw new ApiError(
      response.status,
      errorBody?.code ?? "unknown_error",
      errorBody?.message ?? FALLBACK_ERROR_MESSAGE,
      errorBody?.details ?? [],
    );
  }

  return data as TResponse;
}
