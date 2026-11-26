/**
 * Enforces the design-system rules described in frontend/README.md:
 *
 *  1. CSS outside src/app/theme.css may not contain raw colors (#hex, rgb(), hsl())
 *     or raw lengths (px, rem, em). Use var(--token) and add tokens to theme.css.
 *  2. TSX may not use inline style={{...}} or Tailwind utility class strings
 *     (p-4, mt-2, text-[..], bg-..., rounded-...). Use semantic CSS classes.
 *
 * Run: npm run lint:tokens
 */

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

const SRC_DIR = join(process.cwd(), "src");
const TOKEN_FILE = join("src", "app", "theme.css");

const CSS_RULES = [
  { name: "raw hex color", pattern: /#[0-9a-fA-F]{3,8}\b/g },
  { name: "raw rgb/hsl color", pattern: /\b(?:rgba?|hsla?)\(/g },
  { name: "raw length", pattern: /(?<![\w-])-?\d*\.?\d+(?:px|rem|em)\b/g },
];

const TSX_RULES = [
  { name: "inline style", pattern: /\bstyle=\{\{/g },
  {
    name: "Tailwind utility class",
    pattern:
      /className=["'`{][^"'`}]*\b(?:-?(?:p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|space-[xy]|w|h|min-w|min-h|max-w|max-h|text|bg|border|rounded|shadow|leading|tracking|font|z|top|left|right|bottom|inset)-(?:\d|\[|xs\b|sm\b|md\b|lg\b|xl\b|2xl\b|full\b|screen\b))/g,
  },
];

function walk(directory) {
  return readdirSync(directory).flatMap((entry) => {
    const path = join(directory, entry);
    return statSync(path).isDirectory() ? walk(path) : [path];
  });
}

function stripCssComments(source) {
  return source.replace(/\/\*[\s\S]*?\*\//g, (comment) => comment.replace(/[^\n]/g, " "));
}

function findViolations(file, source, rules) {
  const violations = [];
  const lines = source.split("\n");
  for (const { name, pattern } of rules) {
    lines.forEach((line, index) => {
      for (const match of line.matchAll(pattern)) {
        violations.push(`${file}:${index + 1}  ${name}: ${match[0]}`);
      }
    });
  }
  return violations;
}

const violations = walk(SRC_DIR).flatMap((path) => {
  const file = relative(process.cwd(), path).split(sep).join("/");
  if (path.endsWith(".css") && relative(process.cwd(), path) !== TOKEN_FILE) {
    return findViolations(file, stripCssComments(readFileSync(path, "utf8")), CSS_RULES);
  }
  if (path.endsWith(".tsx")) {
    return findViolations(file, readFileSync(path, "utf8"), TSX_RULES);
  }
  return [];
});

if (violations.length > 0) {
  console.error(`Design token check failed (${violations.length}):\n`);
  console.error(violations.join("\n"));
  console.error("\nUse var(--token) from src/app/theme.css and semantic CSS classes instead.");
  process.exit(1);
}

console.log("Design token check passed: no hardcoded values outside theme.css.");
