#!/usr/bin/env node
/**
 * Carmen AI — Meta Business Suite Auto Poster
 * Posts to Instagram + Facebook Page simultaneously via browser.
 * 
 * Usage:
 *   node meta_poster.js --content ./ig-post.md --image ./image.jpg
 * 
 * First run: opens visible browser for Facebook login → redirect to Business Suite.
 * Subsequent runs: uses saved session (headless OK).
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SESSION_DIR = path.join(__dirname, 'meta-session');

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--content' && args[i + 1]) opts.contentPath = args[++i];
    else if (args[i] === '--image' && args[i + 1]) opts.imagePath = args[++i];
    else if (args[i] === '--visible') opts.visible = true;
  }
  return opts;
}

function log(msg) { console.log(`[MetaBot] ${msg}`); }

// ─── LOGIN ───
async function ensureLoggedIn(page, isHeadless) {
  // Try Meta Business Suite directly
  await page.goto('https://business.facebook.com/latest/home', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(3000);

  let url = page.url();

  // If already on business suite, we're good
  if (url.includes('business.facebook.com') && !url.includes('/login')) {
    log('✅ Already logged in to Meta Business Suite');
    return;
  }

  // If headless and not logged in, can't continue
  if (isHeadless) {
    log('❌ Not logged in + headless — run with --visible for first login');
    throw new Error('Not logged in');
  }

  // Not logged in — Meta has redirected to Facebook login
  log('👆 Facebook login page opened — please log in.');
  log('   Complete any 2FA if needed.');
  log('   After login, Meta should redirect back to Business Suite.');
  log('   Waiting up to 3 minutes...');

  const start = Date.now();
  while (Date.now() - start < 180000) {
    await page.waitForTimeout(3000);
    url = page.url();

    // Check for 2FA
    if (url.includes('/checkpoint') || url.includes('/two_step_verification')) {
      log('   ⏳ 2FA detected — waiting...');
      continue;
    }

    // Success: back on business suite
    if (url.includes('business.facebook.com') && !url.includes('/login')) {
      log('✅ Meta Business Suite loaded! Session saved.');
      return;
    }

    // Logged into facebook.com but not yet at business
    if (url.includes('facebook.com') && !url.includes('/login') && !url.includes('/checkpoint')) {
      log('   ✅ Facebook logged in — navigating to Business Suite...');
      await page.goto('https://business.facebook.com/latest/home', { waitUntil: 'load', timeout: 60000 });
      await page.waitForTimeout(3000);

      if (page.url().includes('business.facebook.com') && !page.url().includes('/login')) {
        log('✅ Meta Business Suite loaded! Session saved.');
        return;
      }
    }
  }

  throw new Error('Login timeout');
}

// ─── CREATE POST ───
async function createPost(page, content, imagePath) {
  log('📝 Looking for post composer...');

  // Try direct composer URL first
  log('📝 Navigating to composer...');
  await page.goto('https://business.facebook.com/latest/composer', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(3000);

  let url = page.url();
  
  // If redirect back to home, click "Tạo bài viết"
  if (!url.includes('/composer')) {
    log('   Composer URL redirected — clicking "Tạo bài viết"...');
    
    // Meta Business Suite: Look for "Create" or "Create post" button (EN + VI)
    const createSelectors = [
      'div[role="button"]:has-text("Tạo bài viết")',
      'a:has-text("Tạo bài viết")',
      'div[role="button"]:has-text("Create post")',
      'a:has-text("Create post")',
      'button:has-text("Tạo bài viết")',
      'button:has-text("Create post")',
    ];

    let clicked = false;
    for (const sel of createSelectors) {
      try {
        const btn = await page.$(sel);
        if (btn && await btn.isVisible().catch(() => false)) {
          log(`   Found: ${sel}`);
          await btn.click();
          await page.waitForTimeout(3000);
          clicked = true;
          break;
        }
      } catch (e) {}
    }

    if (!clicked) {
      await page.screenshot({ path: path.join(__dirname, 'meta-debug.png') });
      throw new Error('Cannot find Create post button');
    }
  }

  // Wait for composer to fully load (modal or new page)
  await page.waitForTimeout(2000);
  log('📄 Composer opened — filling content...');

  // Find text area
  const textAreas = await page.$$('[contenteditable="true"], [role="textbox"], textarea');
  let textArea = null;
  for (const ta of textAreas) {
    if (await ta.isVisible().catch(() => false)) {
      textArea = ta;
      break;
    }
  }

  if (!textArea) {
    await page.screenshot({ path: path.join(__dirname, 'meta-composer-debug.png') });
    throw new Error('Cannot find text area in composer');
  }

  await textArea.click();
  await page.waitForTimeout(500);
  await textArea.fill(content);
  log('   Content pasted');
  await page.waitForTimeout(1000);

  // Upload image
  if (imagePath && fs.existsSync(imagePath)) {
    log('🖼️  Uploading image...');
    
    // Meta composer: click "Thêm ảnh" → dropdown opens → click "Tải lên từ máy tính" → file input appears
    const photoBtnSelectors = [
      'div[role="button"]:has-text("Thêm ảnh")',
      'button:has-text("Thêm ảnh")',
      'div[role="button"]:has-text("Add photo")',
      'button:has-text("Add photo")',
    ];

    let dropdownOpened = false;
    for (const sel of photoBtnSelectors) {
      try {
        const btn = await page.$(sel);
        if (btn && await btn.isVisible().catch(() => false)) {
          log(`   Clicking: "Thêm ảnh"`);
          await btn.click();
          await page.waitForTimeout(1000);
          dropdownOpened = true;
          break;
        }
      } catch (e) {}
    }

    if (dropdownOpened) {
      // Click "Tải lên từ máy tính" (Upload from computer) in the dropdown
      const uploadSelectors = [
        'div[role="menuitem"]:has-text("Tải lên từ máy tính")',
        'div[role="button"]:has-text("Tải lên từ máy tính")',
        'span:has-text("Tải lên từ máy tính")',
        'div[role="menuitem"]:has-text("Upload from computer")',
      ];

      let clicked = false;
      for (const sel of uploadSelectors) {
        try {
          const item = await page.$(sel);
          if (item && await item.isVisible().catch(() => false)) {
            log(`   Clicking: "Tải lên từ máy tính"`);
            // Use fileChooser to capture the dialog
            const [fileChooser] = await Promise.all([
              page.waitForEvent('filechooser', { timeout: 5000 }),
              item.click(),
            ]);
            await fileChooser.setFiles(imagePath);
            log('   ✅ Image selected — waiting for upload...');
            await page.waitForTimeout(5000);
            log('   ✅ Image uploaded');
            clicked = true;
            break;
          }
        } catch (e) {}
      }

      if (!clicked) {
        log('   ⚠️  "Tải lên từ máy tính" not found — trying direct file input');
        const fileInput = await page.$('input[type="file"]');
        if (fileInput) {
          await fileInput.setInputFiles(imagePath);
          await page.waitForTimeout(3000);
        }
      }
    } else {
      log('   ⚠️  "Thêm ảnh" button not found');
      await page.screenshot({ path: path.join(__dirname, 'meta-upload-debug.png') });
    }
  }

  // ─── Post to both platforms via "Đăng lên" dropdown ───
  // The "Đăng lên" dropdown already has both FB + IG selected.
  // Content and image are shared — no need to customize separately.
  await page.waitForTimeout(2000);
  log('🚀 Publishing to both platforms...');

  const publishSelectors = [
    'div[role="button"]:has-text("Đăng")',
    'div[role="button"]:has-text("Publish")',
    'button:has-text("Đăng")',
    'button:has-text("Publish")',
    'div[role="button"]:has-text("Share now")',
    'button:has-text("Share now")',
    'div[role="button"]:has-text("Post")',
    'button:has-text("Post")',
  ];

  let published = false;
  for (const sel of publishSelectors) {
    try {
      const btn = await page.$(sel);
      if (btn && await btn.isVisible().catch(() => false)) {
        const text = (await btn.textContent().catch(() => '')).trim();
        log(`   Clicking: "${text}"`);
        await btn.click();
        await page.waitForTimeout(3000);
        published = true;
        break;
      }
    } catch (e) {}
  }

  if (!published) {
    await page.screenshot({ path: path.join(__dirname, 'meta-publish-debug.png') });
    // List buttons for debug
    const allBtns = await page.$$('div[role="button"], button');
    log('   Visible buttons in composer:');
    for (const btn of allBtns.slice(0, 15)) {
      try {
        const visible = await btn.isVisible().catch(() => false);
        const text = (await btn.textContent().catch(() => '')).trim();
        if (visible && text.length > 0 && text.length < 50) log(`     "${text}"`);
      } catch (e) {}
    }
    throw new Error('Publish button not found');
  }

  // Confirm if needed
  await page.waitForTimeout(2000);
  const confirmBtn = await page.$('div[role="button"]:has-text("Confirm"), button:has-text("Confirm"), div[role="button"]:has-text("Done"), button:has-text("Done")');
  if (confirmBtn && await confirmBtn.isVisible().catch(() => false)) {
    log('📋 Confirming...');
    await confirmBtn.click();
    await page.waitForTimeout(2000);
  }

  log('✅ Post published to Meta Business Suite (IG + FB Page)!');
}

// ─── MAIN ───
async function main() {
  const opts = parseArgs();

  if (!opts.contentPath || !fs.existsSync(opts.contentPath)) {
    console.error('❌ --content must point to an existing file');
    process.exit(1);
  }

  const content = fs.readFileSync(opts.contentPath, 'utf-8');
  log(`🚀 Meta Business Suite Auto-Poster`);
  log(`   Content: ${opts.contentPath} (${content.length} chars)`);
  log(`   Image: ${opts.imagePath || '(none)'}`);

  if (!fs.existsSync(SESSION_DIR)) fs.mkdirSync(SESSION_DIR, { recursive: true });

  const isHeadless = !opts.visible;
  log(`🌐 Launching browser (headless: ${isHeadless})...`);

  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: isHeadless,
    args: ['--disable-blink-features=AutomationControlled', '--no-sandbox'],
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  try {
    await ensureLoggedIn(page, isHeadless);
    await createPost(page, content, opts.imagePath);
    await page.screenshot({ path: path.join(__dirname, 'meta-post-final.png') });
    log('🎉 Done!');
  } catch (error) {
    log(`❌ Error: ${error.message}`);
    await page.screenshot({ path: path.join(__dirname, 'meta-post-error.png') });
    throw error;
  } finally {
    await browser.close();
    log('🔒 Browser closed');
  }
}

main().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
