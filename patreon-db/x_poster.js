#!/usr/bin/env node
/**
 * Carmen AI — X (Twitter) Auto Poster via Browser
 * Posts to X.com using saved browser session (no API keys needed).
 * 
 * Usage:
 *   node x_poster.js --content ./post.md --image ./image.jpg
 * 
 * First run: opens visible browser for login.
 * Subsequent runs: uses saved session cookies (headless OK).
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
      log('⚠️  Not logged in');
      return false;
    }

    // Check for timeline / composer
    const composer = await page.$('[data-testid="tweetTextarea_0"], [aria-label="Post text"], [data-testid="tweetButton"]');
    if (composer) {
      log('✅ Logged in — composer found');
      return true;
    }

    // Fallback: just not on login page = probably logged in
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
    if (url.includes('/home') || url.includes('x.com') && !url.includes('/login')) {
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
    // Try clicking "Post" button to open composer modal
    log('   Composer not found — trying Post button...');
    const postBtn = await page.$('[data-testid="tweetButtonInline"], a[aria-label="Post"], a[href="/compose/post"]');
    if (postBtn) {
      await postBtn.click();
      await page.waitForTimeout(1500);
      composer = await page.$('[data-testid="tweetTextarea_0"], [aria-label="Post text"], [role="textbox"]');
    }
  }

  if (!composer) {
    throw new Error('Cannot find composer');
  }

  log('📄 Typing content...');

  // Click and type the content
  await composer.click();
  await page.waitForTimeout(500);

  // Split into chunks and type naturally (avoids paste detection)
  // X Premium allows long posts, so just paste
  await composer.fill(content);
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

  // Click Post button
  log('🚀 Clicking Post...');
  const postButton = await page.$('[data-testid="tweetButton"], button[data-testid="tweetButtonInline"]');
  if (postButton) {
    await postButton.click();
    await page.waitForTimeout(3000);
  } else {
    throw new Error('Cannot find Post button');
  }

  // Get the tweet URL by navigating to own profile and grabbing the latest tweet
  await page.waitForTimeout(2000);
  let tweetUrl = '';
  
  try {
    // Click profile to see our tweets
    const profileLink = await page.$('a[data-testid="AppTabBar_Profile_Link"], a[href*="/VotiveAstrology"]');
    if (profileLink) {
      await profileLink.click();
      await page.waitForTimeout(3000);
    } else {
      // Fallback: navigate directly
      await page.goto('https://x.com/VotiveAstrology', { waitUntil: 'load', timeout: 30000 });
      await page.waitForTimeout(3000);
    }
    
    // Grab the first (latest) status link from our own profile
    const tweetLink = await page.$('a[href*="/status/"]');
    if (tweetLink) {
      const href = await tweetLink.getAttribute('href');
      // Ensure it's our own tweet (not a retweet/reply to someone else)
      if (href.includes('VotiveAstrology')) {
        tweetUrl = `https://x.com${href}`;
      }
    }
    
    // If still not found, try CSS selector for article-level link
    if (!tweetUrl) {
      const articleLink = await page.$('article a[href*="/VotiveAstrology/status/"]');
      if (articleLink) {
        const href = await articleLink.getAttribute('href');
        tweetUrl = `https://x.com${href}`;
      }
    }
  } catch (e) {
    log(`   ⚠️  Could not grab tweet URL: ${e.message}`);
  }

  log(`✅ Tweet posted!`);
  if (tweetUrl) log(`   URL: ${tweetUrl}`);

  return tweetUrl || 'Posted (URL unknown)';
}

async function main() {
  const opts = parseArgs();

  if (!opts.contentPath || !fs.existsSync(opts.contentPath)) {
    console.error('❌ --content must point to an existing file');
    process.exit(1);
  }

  const content = fs.readFileSync(opts.contentPath, 'utf-8');
  log(`🚀 X Browser Auto-Poster`);
  log(`   Content: ${opts.contentPath} (${content.length} chars)`);
  log(`   Image: ${opts.imagePath || '(none)'}`);

  if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
  }

  const isHeadless = !opts.visible;
  log(`🌐 Launching browser (headless: ${isHeadless})...`);

  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: isHeadless,
    args: ['--disable-blink-features=AutomationControlled', '--no-sandbox'],
    viewport: { width: 1280, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(TIMEOUT);

  try {
    let loggedIn = await isLoggedIn(page);

    if (!loggedIn) {
      if (isHeadless) {
        log('❌ Not logged in + headless — run with --visible for first login');
        await browser.close();
        process.exit(1);
      }
      await login(page);
    }

    const tweetUrl = await postTweet(page, content, opts.imagePath);

    log('🎉 Done!');
    if (tweetUrl) log(`   ${tweetUrl}`);

    await page.screenshot({ path: path.join(__dirname, 'x-post-final.png') });
  } catch (error) {
    log(`❌ Error: ${error.message}`);
    await page.screenshot({ path: path.join(__dirname, 'x-post-error.png') });
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
