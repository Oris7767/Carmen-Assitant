#!/usr/bin/env node
/**
 * Quick X browser test — check saved session validity
 */
const { chromium } = require('playwright');
const path = require('path');

const SESSION_DIR = path.join(__dirname, 'x-session');

function log(msg) { console.log(`[XTest] ${msg}`); }

(async () => {
  log('🔍 Testing X browser session...');
  
  if (!require('fs').existsSync(SESSION_DIR)) {
    log('❌ Session directory not found!');
    process.exit(1);
  }
  
  log('🌐 Launching browser (headless)...');
  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: true,
    args: ['--disable-blink-features=AutomationControlled', '--no-sandbox'],
    viewport: { width: 1280, height: 900 },
  });
  
  const page = await browser.newPage();
  
  try {
    log('📡 Navigating to x.com/home...');
    const start = Date.now();
    await page.goto('https://x.com/home', { waitUntil: 'load', timeout: 60000 });
    await page.waitForTimeout(4000);
    
    const url = page.url();
    const title = await page.title();
    log(`   URL: ${url}`);
    log(`   Title: ${title}`);
    
    if (url.includes('/login') || url.includes('/i/flow/login')) {
      log('❌ NOT LOGGED IN — session expired or invalid');
      log('   Run x_poster.js --visible to re-login');
      
      await page.screenshot({ path: path.join(__dirname, 'x-test-not-logged-in.png') });
      log('   Screenshot saved: x-test-not-logged-in.png');
      
      await browser.close();
      process.exit(1);
    }
    
    // Check for key elements
    log('\n📋 Page elements:');
    
    const composer = await page.$('[data-testid="tweetTextarea_0"]');
    log(`   Composer: ${composer ? '✅ FOUND' : '⚠️  not found'}`);
    
    const postBtn = await page.$('[data-testid="tweetButton"]');
    log(`   Post button: ${postBtn ? '✅ FOUND' : '⚠️  not found'}`);
    
    const navHome = await page.$('[data-testid="AppTabBar_Home_Link"]');
    log(`   Nav Home: ${navHome ? '✅ FOUND' : '⚠️  not found'}`);
    
    const profileLink = await page.$('a[data-testid="AppTabBar_Profile_Link"]');
    log(`   Profile link: ${profileLink ? '✅ FOUND' : '⚠️  not found'}`);
    
    // Get account info
    log('\n👤 Account info:');
    try {
      const accountName = await page.$('[data-testid="primaryColumn"] a[role="link"] span');
      if (accountName) {
        const name = await accountName.textContent();
        log(`   Display name: ${name}`);
      }
    } catch (e) {
      log(`   Could not extract name`);
    }
    
    await page.screenshot({ path: path.join(__dirname, 'x-test-success.png') });
    log('   Screenshot saved: x-test-success.png');
    
    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    log(`\n✅ X browser session VALID (${elapsed}s)`);
    
  } catch (error) {
    log(`❌ Error: ${error.message}`);
    await page.screenshot({ path: path.join(__dirname, 'x-test-error.png') });
  } finally {
    await browser.close();
    log('🔒 Browser closed');
  }
})();
