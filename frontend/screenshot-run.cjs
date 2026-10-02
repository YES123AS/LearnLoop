const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const routes = [
    ['dashboard', '/dashboard'],
    ['profile', '/profile'],
    ['chat', '/chat'],
    ['resource', '/resource'],
    ['path', '/path'],
    ['quiz', '/quiz'],
    ['analysis', '/analysis'],
    ['recommend', '/recommend']
  ];
  for (const [name, route] of routes) {
    await page.goto('http://127.0.0.1:5173' + route, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1200);
    await page.screenshot({ path: 'screenshots/' + name + '.png', fullPage: true });
    console.log('saved', name);
  }
  await browser.close();
})();
