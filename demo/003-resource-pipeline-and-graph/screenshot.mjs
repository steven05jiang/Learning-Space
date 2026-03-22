import { chromium } from "playwright";

const TOKEN = process.argv[2];
const OUT = process.argv[3];
if (!TOKEN || !OUT) {
  console.error("Usage: node screenshot.mjs <token> <artifacts-dir>");
  process.exit(1);
}

const browser = await chromium.launch();
const base = "http://localhost:3001";

// Unauthenticated — login page
const anonCtx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const anonPage = await anonCtx.newPage();
await anonPage.goto(`${base}/login`);
await anonPage.waitForLoadState("networkidle");
await anonPage.screenshot({ path: `${OUT}/14-frontend-login.png`, fullPage: true });
console.log("Saved 14-frontend-login.png");
await anonCtx.close();

// Authenticated context
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

// Dashboard
await page.goto(`${base}/dashboard`);
await page.waitForLoadState("networkidle");
await page.screenshot({ path: `${OUT}/15-frontend-dashboard.png`, fullPage: true });
console.log("Saved 15-frontend-dashboard.png");

// Resources list — shows the READY resource with tags
await page.goto(`${base}/resources`);
await page.waitForLoadState("networkidle");
await page.waitForTimeout(1500);
await page.screenshot({ path: `${OUT}/16-frontend-resources-list.png`, fullPage: true });
console.log("Saved 16-frontend-resources-list.png");

// Graph page — live knowledge graph
await page.goto(`${base}/graph`);
await page.waitForLoadState("networkidle");
await page.waitForTimeout(3000); // wait for force-directed layout to settle
await page.screenshot({ path: `${OUT}/17-frontend-graph.png`, fullPage: true });
console.log("Saved 17-frontend-graph.png");

// Resource detail — shows title, summary, tags
await page.goto(`${base}/resources/1`);
await page.waitForLoadState("networkidle");
await page.waitForTimeout(1000);
await page.screenshot({ path: `${OUT}/18-frontend-resource-detail.png`, fullPage: true });
console.log("Saved 18-frontend-resource-detail.png");

await browser.close();
console.log("All screenshots saved.");
