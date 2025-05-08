const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // 1. Art19ログイン
  await page.goto('https://art19.com/login');
  await page.fill('input[name="email"]', process.env.ART19_USERNAME);
  await page.fill('input[name="password"]', process.env.ART19_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForNavigation();

  // 2. エピソード作成画面へ遷移（番組URLは要指定）
  await page.goto(process.env.ART19_EPISODE_NEW_URL);

  // 3. タイトル入力
  await page.fill('input[name="title"]', process.env.EPISODE_TITLE);

  // 4. ドラフト保存
  await page.click('button:has-text("Save as Draft")');
  await page.waitForTimeout(2000);

  await browser.close();
})();
