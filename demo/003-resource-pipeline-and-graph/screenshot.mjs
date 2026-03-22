import { chromium } from "playwright";
import { writeFileSync } from "fs";

const TOKEN = process.argv[2];
const OUT = process.argv[3];
if (!TOKEN || !OUT) {
  console.error("Usage: node screenshot.mjs <token> <artifacts-dir>");
  process.exit(1);
}

const browser = await chromium.launch();
const base = "http://localhost:3000";

// ── Login page (unauthenticated) ──────────────────────────────────────────────
const anonCtx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const anonPage = await anonCtx.newPage();
await anonPage.goto(`${base}/login`);
await anonPage.waitForLoadState("networkidle");
await anonPage.screenshot({ path: `${OUT}/14-frontend-login.png`, fullPage: true });
await anonCtx.close();
console.log("Saved 14-frontend-login.png");

// ── Authenticated context ─────────────────────────────────────────────────────
const authCtx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
await authCtx.addInitScript((token) => {
  localStorage.setItem("auth_token", token);
  localStorage.setItem("user_info", JSON.stringify({
    id: 2,
    email: "demo@learningspace.dev",
    display_name: "Demo User",
    avatar_url: null,
  }));
}, TOKEN);

const page = await authCtx.newPage();

// ── Page definitions ──────────────────────────────────────────────────────────
const STANDARD_ERRORS = [
  "Failed to fetch",
  "Something went wrong",
  "Error loading",
  "Network Error",
  "Unexpected error",
  "500",
  "404",
];

const pages = [
  {
    url: "/dashboard",
    file: "15-frontend-dashboard.png",
    wait: 1500,
    expectText: ["Dashboard"],
    forbidText: [...STANDARD_ERRORS],
  },
  {
    url: "/resources",
    file: "16-frontend-resources-list.png",
    wait: 1500,
    expectText: ["My Resources"],
    forbidText: [...STANDARD_ERRORS, "No resources found"],
  },
  {
    url: "/knowledge-graph",
    file: "17-frontend-graph.png",
    wait: 3000,
    expectText: ["Knowledge Graph"],
    forbidText: [...STANDARD_ERRORS],
  },
  {
    url: "/resources/2",
    file: "18-frontend-resource-detail.png",
    wait: 1500,
    expectText: ["Machine Learning"],
    forbidText: [...STANDARD_ERRORS],
  },
];

// ── Validation + screenshots ──────────────────────────────────────────────────
const report = { pages: [], totalPassed: 0, totalFailed: 0 };

for (const { url, file, wait = 0, expectText = [], forbidText = [] } of pages) {
  await page.goto(`${base}${url}`);
  await page.waitForLoadState("networkidle");
  if (wait > 0) await page.waitForTimeout(wait);

  const entry = { url, file, passed: [], failed: [] };

  for (const text of expectText) {
    const visible = await page.getByText(text, { exact: false }).first().isVisible().catch(() => false);
    if (visible) {
      entry.passed.push(`EXPECT "${text}" present`);
    } else {
      entry.failed.push(`EXPECT "${text}" MISSING`);
    }
  }

  for (const text of forbidText) {
    const visible = await page.getByText(text, { exact: false }).first().isVisible().catch(() => false);
    if (visible) {
      entry.failed.push(`FORBID "${text}" FOUND`);
    } else {
      entry.passed.push(`FORBID "${text}" absent`);
    }
  }

  await page.screenshot({ path: `${OUT}/${file}`, fullPage: true });

  const status = entry.failed.length === 0 ? "PASS" : "FAIL";
  console.log(`[${status}] ${url} -> ${file}`);
  entry.failed.forEach((f) => console.log(`       FAIL: ${f}`));

  report.pages.push(entry);
  report.totalPassed += entry.passed.length;
  report.totalFailed += entry.failed.length;
}

writeFileSync(`${OUT}/12-ui-validation.json`, JSON.stringify(report, null, 2));
console.log(`\nUI Validation: ${report.totalPassed} passed, ${report.totalFailed} failed`);

await browser.close();

if (report.totalFailed > 0) {
  console.error("UI validation FAILED — see 12-ui-validation.json for details");
  process.exit(1);
}
console.log("All UI checks passed");
