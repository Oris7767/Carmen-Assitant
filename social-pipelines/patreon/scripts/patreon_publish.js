#!/usr/bin/env node
/**
 * Carmen AI — Publish an existing Patreon draft
 * Usage: node patreon_publish.js --url "https://www.patreon.com/posts/XXXXXX/edit"
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const SESSION_DIR = path.join(__dirname, 'patreon-session');
const TIMEOUT = 30000;

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--url' && args[i + 1]) opts.url = args[++i];
    else if (args[i] === '--visible') opts.visible = true;
  }
  return opts;
}

function log(msg) { console.log(`[Publish] ${msg}`); }

async function main() {
  const opts = parseArgs();
  if (!opts.url) {
    console.error('❌ --url is required');
    process.exit(1);
  }

  log(`🎯 Publishing: ${opts.url}`);

  const browser = await chromium.launchPersistentContext(SESSION_DIR, {
    headless: !opts.visible,
    args: ['--disable-blink-features=AutomationControlled', '--no-sandbox'],
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(TIMEOUT);

  try {
    await page.goto(opts.url, { waitUntil: 'networkidle', timeout: TIMEOUT });
    await page.waitForTimeout(3000);

    // Check if we're on the edit page
    const currentUrl = page.url();
    log(`📍 Current URL: ${currentUrl}`);

    if (currentUrl.includes('/login')) {
      throw new Error('Not logged in — session expired');
    }

    // Strategy 1: Find Publish / Publier button by iterating all buttons
    let published = false;

    const allButtons = await page.$$('button, div[role="button"], a[role="button"]');
    for (const btn of allButtons) {
      try {
        const visible = await btn.isVisible().catch(() => false);
        if (!visible) continue;
        const text = (await btn.textContent().catch(() => '')).trim();
        // Match exact "Publier" or "Publish" (possibly with "Now" or "Maintenant")
        if (text === 'Publier' || text === 'Publish' || 
            text === 'Publish now' || text === 'Publier maintenant' ||
            text.startsWith('Publier') || text.startsWith('Publish')) {
          log(`✅ Found publish button: "${text}" — clicking`);
          await btn.click();
          await page.waitForTimeout(2000);
          published = true;
          break;
        }
      } catch (e) { /* try next */ }
    }

    // Strategy 2: Look for dropdown with Publish option
    if (!published) {
      log('🔍 Primary publish button not found — looking for dropdown...');
      
      // Patreon often has a dropdown next to "Save" or "Next"
      const dropdownTriggers = [
        'button[aria-label*="More" i]',
        'button[aria-label*="Plus" i]',
        '[data-testid="post-actions-menu"]',
        'button:has-text("Next")',
        'button:has-text("Suivant")',
        'button:has-text("Save")',
        'button:has-text("Enregistrer")',
      ];

      for (const sel of dropdownTriggers) {
        try {
          const trigger = await page.$(sel);
          if (trigger && await trigger.isVisible().catch(() => false)) {
            log(`   Clicking: ${sel}`);
            await trigger.click();
            await page.waitForTimeout(1000);

            // Look for publish in dropdown
            const dropdownPublish = await page.$(
              'button:has-text("Publish"), div:has-text("Publish"), ' +
              '[role="menuitem"]:has-text("Publish"), ' +
              'button:has-text("Publier"), [role="menuitem"]:has-text("Publier")'
            );
            if (dropdownPublish) {
              log('✅ Found publish in dropdown — clicking');
              await dropdownPublish.click();
              await page.waitForTimeout(2000);
              published = true;
              break;
            }
          }
        } catch (e) { /* try next */ }
      }
    }

    // Strategy 3: Just press the publish keyboard shortcut or look for any green/primary button
    if (!published) {
      log('🔍 Trying to find any primary action button...');
      const allButtons = await page.$$('button');
      for (const btn of allButtons) {
        try {
          const text = await btn.textContent().catch(() => '');
          const visible = await btn.isVisible().catch(() => false);
          if (visible && text.trim()) {
            log(`   Button found: "${text.trim()}"`);
          }
        } catch (e) {}
      }
      
      // Screenshot for debug
      await page.screenshot({ path: path.join(__dirname, 'publish-debug.png') });
      log('📸 Screenshot saved: patreon-db/publish-debug.png');
    }

    if (published) {
      // Wait for publish confirmation or redirect
      await page.waitForTimeout(3000);
      
      // Check for confirmation dialogs (e.g. "Are you sure?")
      const confirmBtn = await page.$('button:has-text("Publish"), button:has-text("Publier"), button:has-text("Confirm"), button:has-text("Confirmer")');
      if (confirmBtn && await confirmBtn.isVisible().catch(() => false)) {
        log('📋 Confirmation dialog — clicking confirm');
        await confirmBtn.click();
        await page.waitForTimeout(3000);
      }

      const finalUrl = page.url();
      log(`🎉 Published! Final URL: ${finalUrl}`);
      log(`   Public post URL (remove /edit): ${finalUrl.replace('/edit', '')}`);
    } else {
      log('⚠️  Could not find publish button — check publish-debug.png');
    }

    await page.screenshot({ path: path.join(__dirname, 'publish-final.png') });

  } catch (error) {
    log(`❌ Error: ${error.message}`);
    await page.screenshot({ path: path.join(__dirname, 'publish-error.png') });
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
