import type { IsoDateTime } from "@/types/api";

/**
 * The single place that formats dates. The API sends UTC; these show it in the
 * viewer's local time zone (IST for the store team).
 */

const dateTimeFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

const dateFormatter = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  year: "numeric",
});

/** "2026-11-25T14:12:38Z" -> "25 Nov 2026, 7:42 pm" */
export function formatDateTime(value: IsoDateTime): string {
  return dateTimeFormatter.format(new Date(value));
}

/** "2026-11-25T14:12:38Z" -> "25 Nov 2026" */
export function formatDate(value: IsoDateTime): string {
  return dateFormatter.format(new Date(value));
}
