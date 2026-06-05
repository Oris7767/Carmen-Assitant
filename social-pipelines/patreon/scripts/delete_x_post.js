#!/usr/bin/env node
const { chromium } = require('playwright');
const path = require('path');

const SESSION_DIR = path.join(__dirname, 'x-session');
const TWEET_URL = 'https://x.com/VotiveAstrology/status/2061114083328573473';

(async () => {
  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: true,
    args: ['--disable-blink-features=AutomationControlled', '--no-sandbox'],
    viewport: { width: 1440, height: 900 },
  });
  const page = await browser.newPage();
  
  console.log('[XBot] Navigating to tweet...');
  await page.goto(TWEET_URL, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(3000);
  
  // Click the More menu (three dots)
  const moreBtn = await page.$('[aria-label="More"]');
  if (moreBtn) {
    console.log('[XBot] Clicking More menu...');
    await moreBtn.click();
    await page.waitForTimeout(1500);
    
    // Click Delete
    const deleteBtn = await page.$('text=Delete');
    if (deleteBtn) {
      console.log('[XBot] Clicking Delete...');
      await deleteBtn.click();
      await page.waitForTimeout(1500);
      const confirm = await page.$('[data-testid="confirmationSheetConfirm"]');
      if (confirm) {
        await confirm.click();
        await page.waitForTimeout(2000);
        console.log('[XBot] Tweet deleted!');
      }
    } else {
      console.log('[XBot] Delete button not found');
    }
  } else {
    console.log('[XBot] More button not found');
  }
  
  await browser.close();
  process.exit(0);
})();
