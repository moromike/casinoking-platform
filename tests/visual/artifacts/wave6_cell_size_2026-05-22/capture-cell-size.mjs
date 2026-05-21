import { createRequire } from "node:module";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const requireFromFrontend = createRequire(new URL("../../../../frontend/package.json", import.meta.url));
const { chromium } = requireFromFrontend("playwright");

const baseUrl = process.env.WAVE6_BASE_URL ?? "http://127.0.0.1:3102";
const outputDir = path.resolve("tests/visual/artifacts/wave6_cell_size_2026-05-22");

const viewports = [
  { name: "desktop", width: 1365, height: 768 },
  { name: "mobile", width: 390, height: 844 },
  { name: "landscape", width: 844, height: 390 },
];

async function dismissGates(page) {
  for (let attempt = 0; attempt < 18; attempt += 1) {
    const gameplayVisible = await page.locator("[data-testid='boxe-gameplay']").isVisible().catch(() => false);
    const providerVisible = await page.locator(".game-provider-bootstrap").isVisible().catch(() => false);
    const howToPlayVisible = await page.locator(".game-how-to-play-overlay").isVisible().catch(() => false);
    if (gameplayVisible && !providerVisible && !howToPlayVisible) {
      return;
    }

    const skip = page.getByRole("button", { name: /salta/i });
    if (await skip.isVisible().catch(() => false)) {
      await skip.click();
      await page.waitForTimeout(250);
      continue;
    }

    const continueButton = page.getByRole("button", { name: /continua/i });
    if (await continueButton.isVisible().catch(() => false)) {
      await continueButton.click();
      await page.waitForTimeout(250);
      continue;
    }

    await page.waitForTimeout(750);
  }

  await page.waitForSelector("[data-testid='boxe-gameplay']", { timeout: 10_000 });
  await page.locator(".game-provider-bootstrap, .game-how-to-play-overlay").waitFor({
    state: "hidden",
    timeout: 10_000,
  });
}

async function selectRows(page, rows) {
  await page.getByTestId(`boxe-rows-${rows}`).click({ timeout: 10_000 });
  await page.waitForTimeout(250);
}

async function measure(page) {
  return page.evaluate(() => {
    const board = document.querySelector(".boxe-pyramid-board");
    const boardRect = board?.getBoundingClientRect();
    const rows = Array.from(document.querySelectorAll(".boxe-pyramid-row")).map((row) => {
      const rowRect = row.getBoundingClientRect();
      const cells = Array.from(row.querySelectorAll(".boxe-pyramid-cell")).map((cell) => {
        const rect = cell.getBoundingClientRect();
        return {
          width: Number(rect.width.toFixed(2)),
          height: Number(rect.height.toFixed(2)),
        };
      });
      return {
        dataRow: row.getAttribute("data-row"),
        cellCount: cells.length,
        rowWidth: Number(rowRect.width.toFixed(2)),
        cellSizes: cells,
        uniqueWidths: Array.from(new Set(cells.map((cell) => cell.width))),
        uniqueHeights: Array.from(new Set(cells.map((cell) => cell.height))),
      };
    });
    return {
      boardWidth: boardRect ? Number(boardRect.width.toFixed(2)) : 0,
      rows,
    };
  });
}

await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({
  reducedMotion: "reduce",
});
const page = await context.newPage();
const results = [];

for (const rows of [4, 8]) {
  await page.setViewportSize({ width: 1365, height: 768 });
  await page.goto(`${baseUrl}/boxe?title_code=boxe001&mode=demo`, {
    waitUntil: "domcontentloaded",
  });
  await dismissGates(page);
  await selectRows(page, rows);

  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.waitForTimeout(500);
    const metrics = await measure(page);
    const screenshot = `boxe_rows${rows}_${viewport.name}.png`;
    await page.screenshot({ path: path.join(outputDir, screenshot), fullPage: false });
    results.push({
      rows,
      viewport: viewport.name,
      screenshot,
      metrics,
    });
  }
}

await writeFile(
  path.join(outputDir, "cell-size-measurements.json"),
  `${JSON.stringify(results, null, 2)}\n`,
  "utf8",
);

await browser.close();
