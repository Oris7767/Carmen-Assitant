#!/usr/bin/env node
/**
 * Carmen AI — Patreon Auto Poster
 * Posts daily forecast as DRAFT to Patreon with illustration image.
 * 
 * Usage:
 *   node patreon_poster.js --title "Title" --content-path ./content.md --image ./image.jpg
 * 
 * First run: opens visible browser for Google OAuth login.
 * Subsequent runs: uses saved session cookies (headless OK).
 * 
 * Env vars:
 *   PATREON_HEADLESS=1    — force headless mode
 *   PATREON_DEBUG=1       — extra logging
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// ─────────────────── CONFIG ───────────────────
const SESSION_DIR = path.join(__dirname, 'patreon-session');
const PATREON_EMAIL = 'votiveacademy@gmail.com';
const PATREON_BASE = 'https://www.patreon.com';
const TIMEOUT = 30000;

// ─────────────────── PARSE ARGS ───────────────────
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--title' && args[i + 1]) opts.title = args[++i];
    else if (args[i] === '--content-path' && args[i + 1]) opts.contentPath = args[++i];
    else if (args[i] === '--image' && args[i + 1]) opts.imagePath = args[++i];
    else if (args[i] === '--draft') opts.draftOnly = true;
    else if (args[i] === '--visible') opts.visible = true;
  }
  return opts;
}

// ─────────────────── HELPERS ───────────────────
function log(msg) { console.log(`[PatreonBot] ${msg}`); }
function debug(msg) { if (process.env.PATREON_DEBUG) console.log(`[DEBUG] ${msg}`); }

async function isLoggedIn(page) {
  try {
    // Go directly to /home — Patreon redirects to /login if not authenticated
    await page.goto(`${PATREON_BASE}/home`, { waitUntil: 'networkidle', timeout: TIMEOUT });
    await page.waitForTimeout(3000);
    
    const currentUrl = page.url();
    debug(`After /home: ${currentUrl}`);
    
    // If redirected to login page, definitely not authenticated
    if (currentUrl.includes('/login')) {
      log('⚠️  Redirected to /login — not authenticated');
      return false;
    }
    
    // Check for logged-in indicators (avatar, notifications bell, etc)
    const indicators = [
      'img[alt*="avatar" i]',
      '[data-testid="user-avatar"]',
      '[aria-label*="notification" i]',
      'a[href*="/notifications"]',
      '[data-testid="global-navigation"]',
    ];
    
    for (const sel of indicators) {
      const el = await page.$(sel);
      if (el) {
        const visible = await el.isVisible().catch(() => false);
        if (visible) {
          debug(`Logged-in indicator: ${sel}`);
          log('✅ Session active — logged in');
          return true;
        }
      }
    }
    
    // Also check for creator-specific content
    const bodyText = await page.textContent('body').catch(() => '');
    if (bodyText.includes('Create') || bodyText.includes('Dashboard') || bodyText.includes('My page')) {
      log('✅ Session active — logged in (creator content detected)');
      return true;
    }
    
    // Ambiguous
    await page.screenshot({ path: path.join(__dirname, 'login-ambiguous.png') });
    log('⚠️  Login state ambiguous — screenshot saved');
    return false;
  } catch (e) {
    debug(`isLoggedIn error: ${e.message}`);
    return false;
  }
}

async function googleLogin(page) {
  log('🔑 Starting Google OAuth login flow...');
  log(`   Email: ${PATREON_EMAIL}`);
  
  await page.goto(`${PATREON_BASE}/login`, { waitUntil: 'networkidle', timeout: TIMEOUT });
  await page.waitForTimeout(2000);
  
  // Find and click "Continue with Google"
  // Patreon login page: "Continue with Google" is typically a div/button with Google logo
  const googleSelectors = [
    'div[role="button"]:has-text("Continue with Google")',
    'button:has-text("Continue with Google")',
    'div:has-text("Continue with Google")',
    'a[href*="google"]',
    'a[href*="accounts.google"]',
    '[data-login="google"]',
    'button:has-text("Google")',
  ];
  
  let clicked = false;
  for (const sel of googleSelectors) {
    try {
      const elements = await page.$$(sel);
      for (const btn of elements) {
        const visible = await btn.isVisible();
        if (visible) {
          debug(`Found Google button: ${sel}`);
          await btn.click();
          clicked = true;
          break;
        }
      }
      if (clicked) break;
    } catch (e) { debug(`Selector ${sel}: ${e.message}`); }
  }
  
  if (!clicked) {
    // Last resort: click by img alt or svg containing Google
    try {
      const googleImg = await page.$('img[alt*="Google" i], svg[aria-label*="Google" i]');
      if (googleImg) {
        await googleImg.click();
        clicked = true;
      }
    } catch (e) {}
  }
  
  if (!clicked) {
    log('⚠️  Could not find Google login button — taking screenshot for debug');
    await page.screenshot({ path: path.join(__dirname, 'login-debug.png') });
    throw new Error('Google login button not found. Check login-debug.png');
  }
  
  log('⏳ Google OAuth popup/tab opened...');
  log('   👉 Please complete Google login in the browser window');
  log('   Email should be pre-filled or type: ' + PATREON_EMAIL);
  log('   Waiting up to 2 minutes...');
  
  // Wait for Google OAuth to complete — one of these will happen:
  // 1. Page updates to show "Continue as [Name]" (first-time or re-auth)
  // 2. URL redirects to patreon.com (already linked account)
  // 3. Popup closes and we need to check for the confirm button
  log('   ⏳ Waiting for Google OAuth (timeout: 5 min)...');
  log('   Watch the browser — complete login and any 2FA');
  
  let authComplete = false;
  const startTime = Date.now();
  const maxWait = 300000; // 5 min
  
  while (Date.now() - startTime < maxWait) {
    await page.waitForTimeout(2000);
    
    // Check if URL changed to Patreon (not login page)
    const currentUrl = page.url();
    if (currentUrl.includes('patreon.com') && !currentUrl.includes('/login')) {
      log('✅ Redirected to Patreon homepage');
      authComplete = true;
      break;
    }
    
    // Check for "Continue as [Name]" button (Google identity confirmed by Patreon)
    const continueBtn = await page.$(
      'button:has-text("Continue as"), div[role="button"]:has-text("Continue as"), ' +
      'a:has-text("Continue as"), button:has-text("Votive Academy"), ' +
      'div:has-text("Continue as Votive Academy")'
    );
    if (continueBtn) {
      try {
        const visible = await continueBtn.isVisible();
        if (visible) {
          log('✅ Detected "Continue as Votive Academy" — clicking!');
          await continueBtn.click();
          await page.waitForTimeout(5000);
          authComplete = true;
          break;
        }
      } catch (e) { /* keep waiting */ }
    }
    
    // Check for any confirmation/consent screen
    const confirmSelectors = [
      'button:has-text("Confirm")',
      'button:has-text("Accept")',
      'button:has-text("Allow")',
      'button:has-text("Continue")',
    ];
    for (const sel of confirmSelectors) {
      try {
        const btn = await page.$(sel);
        if (btn && await btn.isVisible()) {
          const text = await btn.textContent();
          debug(`Found button: "${text.trim()}"`);
        }
      } catch (e) {}
    }
  }
  
  if (!authComplete) {
    log('⏰ Timeout — Google OAuth did not complete');
  }
  
  // Verify login
  const loggedIn = await isLoggedIn(page);
  if (!loggedIn) {
    log('❌ Login verification failed');
    await page.screenshot({ path: path.join(__dirname, 'login-failed.png') });
    throw new Error('Google login failed. Check login-failed.png');
  }
  
  log('✅ Google login successful! Session saved.');
}

async function createDraftPost(page, opts) {
  log('📝 Navigating to post creator...');
  
  // Go to creator post page
  await page.goto(`${PATREON_BASE}/posts/new`, { waitUntil: 'networkidle', timeout: TIMEOUT });
  await page.waitForTimeout(3000);
  
  // Check if we landed on the post creator or need to select creator page first
  const currentUrl = page.url();
  debug(`Current URL: ${currentUrl}`);
  
  if (currentUrl.includes('/login')) {
    throw new Error('Redirected to login — session expired');
  }
  
  // ─── BODY CONTENT (paste FIRST, before title to avoid overwrite) ───
  log('📄 Pasting body content...');
  let content = fs.readFileSync(opts.contentPath, 'utf-8');
  
  // Preprocess: strip markdown for clean WYSIWYG paste
  // (file kept as markdown for archiving)
  content = content
    .replace(/^#{1,3} /gm, '')
    .replace(/^---$/gm, '─────────────────────')
    .replace(/^[\s\|\-]+$/gm, '')  // remove table separator lines (|------|)
    .replace(/^\|/gm, '')            // remove leading pipe
    .replace(/\|$/gm, '')            // remove trailing pipe
    .replace(/\s*\|\s*/g, ' | ')    // keep pipes as | with spacing
    .replace(/\*\*/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/^[ \t]+/gm, '')       // remove leading whitespace on each line
    .trim();
  
  const bodySelectors = [
    '[role="textbox"]',
    '[data-testid="post-content"]',
    '[contenteditable="true"]:not([aria-label*="title"])',
    '.ProseMirror',
    '.post-content-editor',
    '.rich-text-editor',
    '.ql-editor',
    '[data-slate-editor="true"]',
  ];
  
  let bodySet = false;
  for (const sel of bodySelectors) {
    try {
      const el = await page.$(sel);
      if (el) {
        debug(`Body field: ${sel}`);
        await el.click();
        await page.waitForTimeout(500);
        
        // Use keyboard insertText (works with ProseMirror, unlike fill())
        // Select all and delete first
        await page.keyboard.press('Meta+A');
        await page.waitForTimeout(200);
        await page.keyboard.press('Backspace');
        await page.waitForTimeout(300);
        
        // Type content in chunks to avoid timeout on large posts
        const CHUNK_SIZE = 2000;
        for (let i = 0; i < content.length; i += CHUNK_SIZE) {
          const chunk = content.substring(i, i + CHUNK_SIZE);
          await page.keyboard.insertText(chunk);
          await page.waitForTimeout(100);
        }
        
        bodySet = true;
        break;
      }
    } catch (e) { /* try next */ }
  }
  
  if (!bodySet) {
    log('⚠️  Body field not found — trying keyboard navigation');
    await page.keyboard.press('Tab');
    await page.waitForTimeout(500);
    await page.keyboard.insertText(content);
  }
  
  log('✅ Content filled');
  await page.waitForTimeout(1000);
  
  // ─── SET TITLE (AFTER body content, so it doesn't get overwritten) ───
  log('📌 Setting title...');
  const titleSelectors = [
    'textarea[aria-label="Titre"]',
    'textarea[placeholder="Titre"]',
    'textarea[placeholder*="title" i]',
    'input[placeholder*="title" i]',
    '[data-testid="post-title"]',
    '[contenteditable="true"][aria-label*="title" i]',
    'h1[contenteditable="true"]',
    '.post-title-input',
    '#title',
  ];
  
  let titleSet = false;
  for (const sel of titleSelectors) {
    try {
      const el = await page.$(sel);
      if (el) {
        debug(`Title field: ${sel}`);
        await el.click();
        await page.waitForTimeout(300);
        // Select all and clear before filling
        await page.keyboard.press('Meta+A');
        await page.waitForTimeout(100);
        await el.fill(opts.title);
        titleSet = true;
        break;
      }
    } catch (e) { /* try next */ }
  }
  
  if (!titleSet) {
    log('⚠️  Title field not found by selectors — trying fallback');
    await page.screenshot({ path: path.join(__dirname, 'post-debug.png') });
  }
  
  await page.waitForTimeout(1000);
  
  // ─── IMAGE UPLOAD ───
  if (opts.imagePath && fs.existsSync(opts.imagePath)) {
    log('🖼️  Uploading image...');
    
    // Look for image upload button or drag-drop zone
    const imageUploadSelectors = [
      'input[type="file"][accept*="image"]',
      'input[type="file"]',
      'button:has-text("Add image")',
      'button:has-text("Image")',
      'button:has-text("Media")',
      '[aria-label*="image" i]',
      '[aria-label*="upload" i]',
      '[data-testid="image-upload"]',
    ];
    
    let uploaded = false;
    for (const sel of imageUploadSelectors) {
      try {
        const input = await page.$(sel);
        if (input) {
          debug(`Image upload: ${sel}`);
          const tagName = await input.evaluate(el => el.tagName);
          if (tagName === 'INPUT') {
            await input.setInputFiles(opts.imagePath);
            uploaded = true;
            break;
          } else {
            // It's a button — click it to reveal file input
            await input.click();
            await page.waitForTimeout(1000);
            // After clicking, a file input might appear
            const fileInput = await page.$('input[type="file"]');
            if (fileInput) {
              await fileInput.setInputFiles(opts.imagePath);
              uploaded = true;
              break;
            }
          }
        }
      } catch (e) { /* try next */ }
    }
    
    if (!uploaded) {
      log('⚠️  Could not find image upload — check post-debug.png');
      await page.screenshot({ path: path.join(__dirname, 'post-debug.png') });
    } else {
      log('✅ Image uploaded — waiting for processing...');
      await page.waitForTimeout(5000); // Wait for image to process
    }
  }
  
  // ─── SAVE AS DRAFT ───
  log('💾 Saving as draft...');
  
  // Look for Save/Publish buttons
  const saveSelectors = [
    'button:has-text("Save")',
    'button:has-text("Save draft")',
    'button:has-text("Save as draft")',
    '[data-testid="save-draft"]',
    'button:has-text("Draft")',
    '[aria-label*="Save" i]',
    '[aria-label*="draft" i]',
  ];
  
  const publishSelectors = [
    'button:has-text("Publish")',
    'button:has-text("Post")',
    '[data-testid="publish-button"]',
    '[aria-label*="Publish" i]',
  ];
  
  let saved = false;
  
  // Strategy 1: Look for a "Save" or "Save draft" button
  for (const sel of saveSelectors) {
    try {
      const btn = await page.$(sel);
      if (btn) {
        debug(`Save button: ${sel}`);
        await btn.click();
        saved = true;
        break;
      }
    } catch (e) { /* try next */ }
  }
  
  if (!saved) {
    // Strategy 2: Click Publish dropdown and select "Save as draft"
    for (const sel of publishSelectors) {
      try {
        const btn = await page.$(sel);
        if (btn) {
          debug(`Publish button found: ${sel} — checking for dropdown`);
          // Some Patreon UIs have a dropdown next to Publish
          const dropdown = await page.$('button[aria-label*="more" i], [data-testid="publish-dropdown"]');
          if (dropdown) {
            await dropdown.click();
            await page.waitForTimeout(500);
            const draftOption = await page.$('button:has-text("Save as draft"), div:has-text("Save as draft"), [role="menuitem"]:has-text("draft")');
            if (draftOption) {
              await draftOption.click();
              saved = true;
              break;
            }
          }
        }
      } catch (e) { /* try next */ }
    }
  }
  
  if (!saved) {
    log('⏳ Waiting for autosave to complete...');
    // Patreon auto-saves — wait for "Enregistrée" (Saved) status
    try {
      await page.waitForFunction(() => {
        const body = document.body.textContent || '';
        return body.includes('Enregistrée') || body.includes('Saved') || body.includes('Brouillon');
      }, { timeout: 15000 });
      await page.waitForTimeout(1000);
      log('✅ Autosave confirmed');
    } catch (e) {
      log('⚠️  Save status not confirmed — continuing');
    }
  }
  
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(__dirname, 'post-final.png') });
  
  // ─── GET DRAFT URL ───
  const finalUrl = page.url();
  log(`📍 Post URL: ${finalUrl}`);
  
  return finalUrl;
}

// ─────────────────── MAIN ───────────────────
async function main() {
  const opts = parseArgs();
  
  if (!opts.title) {
    console.error('❌ --title is required');
    process.exit(1);
  }
  if (!opts.contentPath || !fs.existsSync(opts.contentPath)) {
    console.error('❌ --content-path must point to an existing file');
    process.exit(1);
  }
  
  log('🚀 Carmen AI — Patreon Auto Poster');
  log(`   Title: ${opts.title}`);
  log(`   Content: ${opts.contentPath}`);
  log(`   Image: ${opts.imagePath || '(none)'}`);
  log(`   Mode: ${opts.draftOnly ? 'DRAFT ONLY' : 'FULL'}`);
  
  // Prepare session directory
  if (!fs.existsSync(SESSION_DIR)) {
    fs.mkdirSync(SESSION_DIR, { recursive: true });
  }
  
  const isHeadless = !!process.env.PATREON_HEADLESS && !opts.visible;
  
  log(`🌐 Launching browser (headless: ${isHeadless})...`);
  
  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: isHeadless,
    args: [
      '--disable-blink-features=AutomationControlled',
      '--no-sandbox',
    ],
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
  });
  
  const page = await browser.newPage();
  page.setDefaultTimeout(TIMEOUT);
  
  try {
    // ─── LOGIN CHECK ───
    let loggedIn = await isLoggedIn(page);
    
    if (!loggedIn) {
      if (isHeadless) {
        log('❌ Not logged in and running headless — cannot complete Google OAuth');
        log('   Run without PATREON_HEADLESS for first login');
        await browser.close();
        process.exit(1);
      }
      await googleLogin(page);
    }
    
    // ─── CREATE POST ───
    const draftUrl = await createDraftPost(page, opts);
    
    log('🎉 Done! Check your Patreon drafts.');
    log(`   URL: ${draftUrl || 'Check Patreon drafts page'}`);
    log('   Screenshot saved: patreon-db/post-final.png');
    
  } catch (error) {
    log(`❌ Error: ${error.message}`);
    await page.screenshot({ path: path.join(__dirname, 'error-state.png') });
    log('   Error screenshot saved: patreon-db/error-state.png');
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
