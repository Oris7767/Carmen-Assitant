#!/usr/bin/env node
/**
 * X (Twitter) Auto Poster via Browser (temporary)
 * Usage:
 *   node x_poster.js --content ./post.md --image ./image.jpg
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SESSION_DIR = path.join(__dirname, 'x-session');
const TIMEOUT = 30000;

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

function log(msg) { console.log(`[XBot] ${msg}`); }

async function isLoggedIn(page) {
  try {
    await page.goto('https://x.com/home', { waitUntil: 'load', timeout: 60000 });
    await page.waitForTimeout(3000);

    const url = page.url();
    if (url.includes('/login') || url.includes('/i/flow/login')) {
      log('⚠️  Not logged in (login page)');
      return false;
    }
    
    const loginCta = await page.$('text="Email or username"');
    if (loginCta) {
      log('⚠️  Not logged in (landing page)');
      return false;
    }
    
    const composer = await page.$('[data-testid="tweetTextarea_0"], [aria-label="Post text"], [data-testid="tweetButton"]');
    if (composer) {
      log('✅ Logged in — composer found');
      return true;
    }

    const navHome = await page.$('[data-testid="AppTabBar_Home_Link"], nav[aria-label="Primary"]');
    if (navHome) {
      log('✅ Logged in — nav found');
      return true;
    }

    const signInBtn = await page.$('a[href="/login"], a[data-testid="loginButton"]');
    if (signInBtn) {
      log('⚠️  Not logged in (sign-in button visible)');
      return false;
    }

    log('✅ Appears logged in');
    return true;
  } catch (e) {
    log(`   isLoggedIn error: ${e.message}`);
    return false;
  }
}

async function login(page) {
  log('🔑 Opening X login page...');
  await page.goto('https://x.com/login', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(3000);

  log('👆 Please log in to X in the browser window.');
  log('   Complete any 2FA if needed.');
  log('   Waiting up to 3 minutes...');

  const start = Date.now();
  while (Date.now() - start < 180000) {
    await page.waitForTimeout(3000);
    const url = page.url();
    if (url.includes('/home') || (url.includes('x.com') && !url.includes('/login'))) {
      const composer = await page.$('[data-testid="tweetTextarea_0"]');
      if (composer) {
        log('✅ Login successful! Session saved.');
        return;
      }
    }
  }

  throw new Error('Login timeout');
}

async function postTweet(page, content, imagePath) {
  log('📝 Opening composer...');

  await page.goto('https://x.com/home', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(3000);

  log('📝 Opening composer...');
  const composerSelectors = [
    '[data-testid="tweetTextarea_0"]',
    '[aria-label="Post text"]',
    '.public-DraftEditor-content',
    '[data-testid="tweetTextarea_0_rich"]',
    '[role="textbox"]',
  ];

  let composer = null;
  for (const sel of composerSelectors) {
    composer = await page.$(sel);
    if (composer) break;
  }

  if (!composer) {
    log('   Composer not found — trying Post button...');
    const postBtn = await page.$('[data-testid="tweetButtonInline"], a[aria-label="Post"], a[href="/compose/post"]');
    if (postBtn) {
      await page.evaluate(el => el.click(), postBtn);
      await page.waitForTimeout(2000);
      composer = await page.$('[data-testid="tweetTextarea_0"], [aria-label="Post text"], [role="textbox"]');
    }
  }

  if (!composer) {
    throw new Error('Cannot find composer');
  }

  log('📄 Typing content...');

  // Click via JS to bypass overlay interception
  await page.evaluate(el => el.click(), composer);
  await page.waitForTimeout(500);

  // Clear and type via JS to bypass overlay
  await page.evaluate(({el, text}) => {
    el.focus();
    el.textContent = '';
    el.innerText = '';
    const dataTransfer = new DataTransfer();
    dataTransfer.setData('text/plain', text);
    el.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dataTransfer, bubbles: true }));
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }, { el: composer, text: content });
  await page.waitForTimeout(1000);

  // Upload image if provided
  if (imagePath && fs.existsSync(imagePath)) {
    log('🖼️  Uploading image...');

    // Find file input for image upload
    const fileInput = await page.$('input[type="file"][accept*="image"]');
    if (fileInput) {
      await fileInput.setInputFiles(imagePath);
      log('   Image uploaded');
      await page.waitForTimeout(2000);
    } else {
      // Try clicking the image upload button first
      const imgBtn = await page.$('[data-testid="toolBar"] [aria-label="Add media"], button[aria-label="Add media"], [aria-label="Add image"]');
      if (imgBtn) {
        await imgBtn.click();
        await page.waitForTimeout(1000);
        const input = await page.$('input[type="file"]');
        if (input) {
          await input.setInputFiles(imagePath);
          log('   Image uploaded');
          await page.waitForTimeout(2000);
        }
      } else {
        log('⚠️  Could not find image upload — posting text only');
      }
    }
  }

  // Click Post button — X overlay intercepts clicks, must use JS evaluate
  log('🚀 Clicking Post...');
  const postButton = await page.$('[data-testid="tweetButton"], button[data-testid="tweetButtonInline"], div[role="button"][data-testid="tweetButton"]');
  if (!postButton) throw new Error('Cannot find Post button');
  
  // Always use JS evaluate to bypass overlay interception
  await page.evaluate(el => el.click(), postButton);
  log('   Post button clicked via JS');
  await page.waitForTimeout(2000);
  
  // Wait for post to complete (composer closes when done)
  await page.waitForTimeout(3000);

  // Get the tweet URL from the timeline
  const tweetLink = await page.$('a[href*="/status/"]');
  if (tweetLink) {
    const href = await tweetLink.getAttribute('href');
    log(`   Tweet URL: https://x.com${href}`);
  }
}

async function main() {
  const opts = parseArgs();
  
  if (!opts.contentPath || !fs.existsSync(opts.contentPath)) {
    console.error('❌ --content must point to an existing file');
    process.exit(1);
  }

  const content = fs.readFileSync(opts.contentPath, 'utf8').trim();
  
  // Resolve image path
  let imagePath = null;
  if (opts.imagePath) {
    imagePath = path.isAbsolute(opts.imagePath) ? opts.imagePath : path.join(process.cwd(), opts.imagePath);
    if (!fs.existsSync(imagePath)) {
      log(`⚠️  Image not found: ${imagePath} — posting text only`);
      imagePath = null;
    }
  }

  log('🚀 X Browser Auto-Poster');
  log(`    Content: ${opts.contentPath} (${content.length} chars)`);
  log(`    Image: ${imagePath || 'none'}`);

  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: !opts.visible,
    args: ['--no-sandbox'],
  });

  const page = await browser.newPage();

  try {
    if (!(await isLoggedIn(page))) {
      await login(page);
    }

    await postTweet(page, content, imagePath);
    log('🎉 Done!');
  } catch (err) {
    log(`❌ Error: ${err.message}`);
    process.exit(1);
  } finally {
    await browser.close();
    log('🔒 Browser closed');
  }
}

main();
