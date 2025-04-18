const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  // --- 事前準備 ---
  // scripts/episode_title_and_shownote.txt からタイトル・ShowNoteを抽出
  let EPISODE_TITLE = 'Test from aipodflow';
  let EPISODE_SHOWNOTE = 'ShowNote from aipodflow';
  try {
    const raw = fs.readFileSync(__dirname + '/episode_title_and_shownote.txt', 'utf8');
    const titleMatch = raw.match(/^Title:\s*(.+)$/m);
    const shownoteMatch = raw.match(/^Show Notes:\s*([\s\S]*)$/m);
    if (titleMatch) EPISODE_TITLE = titleMatch[1].trim();
    if (shownoteMatch) {
      // Show Notes: 以降のテキスト全体（次のセクションや空行まで）
      let desc = shownoteMatch[1].trim();
      // もし "Ad Timecodes:" などでShowNoteが終わる場合はそこまで
      desc = desc.split(/\nAd Timecodes:/)[0].trim();
      EPISODE_SHOWNOTE = desc;
    }
  } catch (e) {
    console.error('Failed to read episode_title_and_shownote.txt, fallback to env or default:', e);
    EPISODE_TITLE = process.env.EPISODE_TITLE || EPISODE_TITLE;
    EPISODE_SHOWNOTE = process.env.EPISODE_SHOWNOTE || EPISODE_SHOWNOTE;
  }

  const browser = await chromium.launch();
  const page = await browser.newPage();

  // 1. Art19ログインページへ
  await page.goto('https://art19.com/login');
  await page.waitForSelector('input[type="email"]', { timeout: 20000 });
  await page.fill('input[type="email"]', process.env.ART19_USERNAME);
  await page.fill('input[type="password"]', process.env.ART19_PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForNavigation({ timeout: 20000 });

  // 2. 管理画面(シリーズページ)へ遷移していることを確認
  if (!page.url().includes('/admin/series/3020f7a0-0e0b-416c-b96d-e26903718f2c/content')) {
    console.error('Not redirected to expected series content page. Current URL:', page.url());
    await browser.close();
    process.exit(1);
  }

  // 3. "New Episode"ボタンを押す
  try {
    await page.waitForSelector('button:has-text("New Episode")', { timeout: 20000 });
    await page.click('button:has-text("New Episode")');
  } catch (e) {
    const html = await page.content();
    fs.writeFileSync('art19_new_episode_debug.html', html);
    console.error('Failed to find or click New Episode button:', e);
    await browser.close();
    process.exit(1);
  }

  // 4. タイトル入力欄にEPISODE_TITLEを入力
  try {
    await page.waitForSelector('input.ui__input.form-control[type="text"]', { timeout: 20000 });
    await page.fill('input.ui__input.form-control[type="text"]', EPISODE_TITLE);
  } catch (e) {
    const html = await page.content();
    fs.writeFileSync('art19_title_input_debug.html', html);
    console.error('Failed to find or fill title input:', e);
    await browser.close();
    process.exit(1);
  }

  // 5. Createボタンを押す
  try {
    await page.waitForSelector('button:has-text("Create")', { timeout: 20000 });
    await page.click('button:has-text("Create")');
  } catch (e) {
    const html = await page.content();
    fs.writeFileSync('art19_create_button_debug.html', html);
    console.error('Failed to find or click Create button:', e);
    await browser.close();
    process.exit(1);
  }

  // 6. Description欄（contenteditable）にEPISODE_SHOWNOTEを入力
  try {
    await page.waitForSelector('div[contenteditable="true"]', { timeout: 20000 });
    await page.fill('div[contenteditable="true"]', EPISODE_SHOWNOTE);
  } catch (e) {
    const html = await page.content();
    fs.writeFileSync('art19_description_input_debug.html', html);
    console.error('Failed to find or fill description contenteditable:', e);
    await browser.close();
    process.exit(1);
  }

  // 7. Update & Closeボタンを押す（有効化されるまで最大10秒待つ）
  try {
    await page.waitForSelector('button:has-text("Update & Close"):not([aria-disabled="true"])', { timeout: 10000 });
    await page.click('button:has-text("Update & Close")');
  } catch (e) {
    const html = await page.content();
    fs.writeFileSync('art19_update_close_debug.html', html);
    console.error('Failed to find or click Update & Close button:', e);
    await browser.close();
    process.exit(1);
  }

  // 完了ログ
  console.log('Episode created with LLM title and shownote, draft saved!');
  await browser.close();
})();
