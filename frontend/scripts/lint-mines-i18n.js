const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");

const PLAYER_RUNTIME_FILES = [
  "app/ui/mines/mines-action-buttons.tsx",
  "app/ui/mines/mines-balance-footer.tsx",
  "app/ui/mines/mines-board.tsx",
  "app/ui/mines/mines-how-to-play-gate.tsx",
  "app/ui/mines/mines-mobile-settings-sheet.tsx",
  "app/ui/mines/mines-rules-modal.tsx",
  "app/ui/mines/mines-runtime-tools.tsx",
  "app/ui/mines/mines-stage-header.tsx",
  "app/ui/mines/mines-standalone.tsx",
];

const SHARED_RUNTIME_FILES = ["app/lib/helpers.ts"];

const FORBIDDEN_PATTERNS = [
  "You won",
  "You hit",
  "Game info",
  "Close game info",
  "DEMO MODE",
  "Grid size",
  "Bet amount",
  "Betting...",
  "Collecting...",
  "Action needed",
  "Back to site",
  "Choose your table balance",
  "Real money",
  "Bonus",
  "Available balance",
  "Maximum",
  "Table entry amount",
  "Entering...",
  "Enter game",
  "Session closed",
  "Session expired",
  "Session expiring",
  "Reload required",
  "Restoring hand",
  "Could not reach the server",
  "Demo balance",
  "Table balance",
  "Payout display",
  "Safe reveal",
  "Settings menu",
  "Bet & collect",
  "Quick start",
  "Standard table",
  "High volatility",
  "Low-friction entry",
  "Balanced setup",
  "Higher risk preset",
];

const FORBIDDEN_REGEXES = [
  {
    label: "hardcoded board face label",
    regex: /(["'`])(MINE|SAFE|PICK)\1|>\s*(MINE|SAFE|PICK)\s*</,
  },
  {
    label: "player-side locale query selector",
    regex: /[?&]locale=/,
  },
  {
    label: "player locale localStorage key",
    regex: /ck_player_locale/,
  },
  {
    label: "language selector component",
    regex: /LanguageSelector|language selector/i,
  },
];

const ALLOWED_OCCURRENCES = new Set([
  "app/ui/mines/mines-rules-modal.tsx|Game info|2",
]);

function readLines(relativePath) {
  const absolutePath = path.join(ROOT, relativePath);
  return fs.readFileSync(absolutePath, "utf8").split(/\r?\n/);
}

function scanLiteralPatterns(relativePath, line, lineNumber, violations) {
  for (const pattern of FORBIDDEN_PATTERNS) {
    if (!line.includes(pattern)) {
      continue;
    }
    const occurrenceKey = `${relativePath}|${pattern}|${lineNumber}`;
    if (ALLOWED_OCCURRENCES.has(occurrenceKey)) {
      continue;
    }
    violations.push({
      relativePath,
      lineNumber,
      kind: "hardcoded player-facing copy",
      match: pattern,
      line,
    });
  }
}

function scanForbiddenRegexes(relativePath, line, lineNumber, violations) {
  for (const rule of FORBIDDEN_REGEXES) {
    if (!rule.regex.test(line)) {
      continue;
    }
    violations.push({
      relativePath,
      lineNumber,
      kind: rule.label,
      match: rule.regex.toString(),
      line,
    });
  }
}

function scanFile(relativePath, violations) {
  const lines = readLines(relativePath);
  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    scanLiteralPatterns(relativePath, line, lineNumber, violations);
    scanForbiddenRegexes(relativePath, line, lineNumber, violations);
  });
}

function main() {
  const violations = [];
  for (const relativePath of [...PLAYER_RUNTIME_FILES, ...SHARED_RUNTIME_FILES]) {
    scanFile(relativePath, violations);
  }

  if (violations.length === 0) {
    console.log("Mines i18n lint passed: no player-facing hardcoded copy found.");
    return;
  }

  console.error("Mines i18n lint failed. Move player-facing copy into the Mines i18n manifest.");
  for (const violation of violations) {
    console.error(
      `${violation.relativePath}:${violation.lineNumber} ${violation.kind}: ${violation.match}`,
    );
    console.error(`  ${violation.line.trim()}`);
  }
  process.exit(1);
}

main();
