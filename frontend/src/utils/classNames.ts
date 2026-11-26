/** Join class names, skipping false/undefined: cx("button", isWide && "button-full-width"). */
export function cx(...classNames: Array<string | false | null | undefined>): string {
  return classNames.filter(Boolean).join(" ");
}
