import { chromium } from 'playwright';

const TOKEN = process.argv[2];
const OUT   = process.argv[3];
if (!TOKEN || !OUT) {
  console.error('Usage: node screenshot.mjs <token> <artifacts-dir>');
  process.exit(1);
}

const browser = await chromium.launch();
const base = 'http://localhost:3001';

// Login page (unauthenticated context)
const anonCtx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const anonPage = await anonCtx.newPage();
await anonPage.goto(`${base}/login`);
await anonPage.waitForLoadState('networkidle');
await anonPage.screenshot({ path: `${OUT}/09-frontend-login.png`, fullPage: true });
await anonCtx.close();
console.log('Saved 09-frontend-login.png');

// Authenticated context — seed localStorage
const authCtx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
await authCtx.addInitScript((token) => {
  localStorage.setItem('auth_token', token);
  localStorage.setItem('user_info', JSON.stringify({
    id: 1, email: 'demo@learningspace.dev', display_name: 'Demo User', avatar_url: null
  }));
}, TOKEN);

const page = await authCtx.newPage();

const pages = [
  { url: '/dashboard',      file: '10-frontend-dashboard.png' },
  { url: '/resources/new',  file: '11-frontend-resources-new.png' },
  { url: '/resources',      file: '12-frontend-resources-list.png' },
];

for (const { url, file } of pages) {
  await page.goto(`${base}${url}`);
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: `${OUT}/${file}`, fullPage: true });
  console.log(`Saved ${file}`);
}

await browser.close();
console.log('All screenshots saved.');
