import type { MoneyString } from "@/types/api";

/**
 * Money helpers. The single place that formats or adds up amounts.
 *
 * Amounts arrive as exact decimal strings ("4499.00"). Any arithmetic (the cart
 * preview total) is done in whole paise, which are integers, so there is no
 * floating-point drift such as 0.1 + 0.2 = 0.30000000000000004. The backend
 * still calculates the real total; the frontend only previews it.
 */

const PAISE_PER_RUPEE = 100;
const MONEY_PATTERN = /^(-?)(\d+)(?:\.(\d{1,2}))?$/;

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** "4499.5" -> 449950. Parsed from the string, never via parseFloat. */
export function toPaise(amount: MoneyString): number {
  const match = MONEY_PATTERN.exec(amount.trim());
  if (!match) {
    throw new Error(`Invalid money amount: "${amount}"`);
  }
  const [, sign, rupees, fraction = ""] = match;
  const paise = Number(rupees) * PAISE_PER_RUPEE + Number(fraction.padEnd(2, "0"));
  return sign === "-" ? -paise : paise;
}

/** Line total in paise: unit price x quantity, exact integer arithmetic. */
export function multiplyPaise(unitPrice: MoneyString, quantity: number): number {
  return toPaise(unitPrice) * quantity;
}

/** 1089700 -> "₹10,897.00" */
export function formatPaise(paise: number): string {
  return currencyFormatter.format(paise / PAISE_PER_RUPEE);
}

/** "10897.00" -> "₹10,897.00" */
export function formatMoney(amount: MoneyString): string {
  return formatPaise(toPaise(amount));
}
