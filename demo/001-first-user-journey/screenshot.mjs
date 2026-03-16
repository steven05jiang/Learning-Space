import { chromium } from 'playwright';
import fs from 'fs';

const TOKEN = process.argv[2];
if (!TOKEN) {
  console.error('Usage: node screenshot.mjs <JWT_TOKEN>');
  process.exit(1);
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();

  // Inject auth token
  await context.addInitScript((token) => {
    localStorage.setItem('auth_token', token);
    localStorage.setItem('user_info', JSON.stringify({
      id: 1, email: 'demo@learningspace.dev', display_name: 'Demo User'
    }));
  }, TOKEN);

  const page = await context.newPage();

  // Create artifacts directory if it doesn't exist
  const artifactsDir = 'demo/001-first-user-journey/artifacts';
  if (!fs.existsSync(artifactsDir)) {
    fs.mkdirSync(artifactsDir, { recursive: true });
  }

  try {
    console.log('Taking screenshot of dashboard...');
    // Dashboard
    await page.goto('http://localhost:3001/dashboard');
    await page.waitForLoadState('networkidle');
    await page.screenshot({
      path: `${artifactsDir}/09-frontend-dashboard-fixed.png`,
      fullPage: true
    });

    console.log('Taking screenshot of resources new page...');
    // Resources new
    await page.goto('http://localhost:3001/resources/new');
    await page.waitForLoadState('networkidle');
    await page.screenshot({
      path: `${artifactsDir}/10-frontend-resources-new-fixed.png`,
      fullPage: true
    });

    console.log('Taking screenshot of resources list page...');
    // Resources list
    await page.goto('http://localhost:3001/resources');
    await page.waitForLoadState('networkidle');
    await page.screenshot({
      path: `${artifactsDir}/11-frontend-resources-list-fixed.png`,
      fullPage: true
    });

    console.log('Screenshots saved successfully');
  } catch (error) {
    console.error('Error taking screenshots:', error);
  } finally {
    await browser.close();
  }
})();