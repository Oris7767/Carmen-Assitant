#!/usr/bin/env node
/**
 * Carmen AI — Vedic Weekly Post Pipeline v2
 * ==========================================
 * Unified pipeline for posting Vedic astrology content
 * to X (Twitter) and Meta (FB + IG).
 * 
 * Features:
 *   - Auth health check before posting
 *   - Browser-based X posting with session reuse
 *   - Meta API posting with token refresh guidance
 *   - Auto-image upload for IG (via FB CDN)
 *   - Post tracking in vedic-weekly-posts.json
 * 
 * Usage:
 *   node vedic_weekly.js [--dry-run]
 *   node vedic_weekly.js --post <x-content.md> <meta-content.md> <image.jpg>
 *   node vedic_weekly.js --health    (check auth status only)
 * 
 * By default, reads latest unposted content files.
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');
const https = require('https');

const ROOT = __dirname;
const META_PIPELINE = path.join(ROOT, '..', 'meta-pipeline');
const POSTS_DB = path.join(ROOT, 'vedic-weekly-posts.json');

// ─── Config ───
const FOOTER = '📩 votive@vedicvn.com | 🌍 vedicvn.com | 📞 +84 385448747';
const META_TOKEN_FILE = path.join(META_PIPELINE, '.token');
const X_SESSION_DIR = path.join(ROOT, 'x-session');
const ENV_FILE = path.join(ROOT, '.env');

// ─── Helpers ───
function log(emoji, msg) {
  console.log(`${emoji} ${msg}`);
}

function loadEnv() {
  const env = {};
  if (fs.existsSync(ENV_FILE)) {
    const content = fs.readFileSync(ENV_FILE, 'utf-8');
    for (const line of content.split('\n')) {
      const match = line.match(/^([A-Z_]+)=(.+)$/);
      if (match) env[match[1]] = match[2];
    }
  }
  return env;
}

// ─── Auth Checks ───

function checkXSession() {
  const hasSessionDir = fs.existsSync(X_SESSION_DIR);
  const hasCookies = hasSessionDir && fs.existsSync(path.join(X_SESSION_DIR, 'Default', 'Cookies'));
  
  if (hasCookies) {
    log('✅', 'X browser session found');
    return true;
  }
  
  // Check API keys as fallback
  const env = loadEnv();
  if (env.X_API_KEY && env.X_API_SECRET && env.X_ACCESS_TOKEN && env.X_ACCESS_SECRET) {
    log('⚠️', 'X API keys found (may be expired — last test: 401)');
    return false;
  }
  
  log('❌', 'No X session or API keys found');
  return false;
}

async function checkMetaToken() {
  if (!fs.existsSync(META_TOKEN_FILE)) {
    log('❌', 'Meta token file not found');
    return false;
  }
  
  const token = fs.readFileSync(META_TOKEN_FILE, 'utf-8').trim();
  
  // Quick test: call /me on Graph API
  try {
    const result = await new Promise((resolve, reject) => {
      https.get(`https://graph.facebook.com/v20.0/me?access_token=${token}`, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try { resolve(JSON.parse(data)); }
          catch { resolve(null); }
        });
      }).on('error', reject);
    });
    
    if (result?.id) {
      log('✅', `Meta token valid (User: ${result.name || result.id})`);
      return true;
    } else if (result?.error?.message?.includes('expired')) {
      log('❌', `Meta token EXPIRED: ${result.error.message}`);
      return false;
    } else {
      log('❌', `Meta token invalid: ${JSON.stringify(result)}`);
      return false;
    }
  } catch (e) {
    log('❌', `Meta token check error: ${e.message}`);
    return false;
  }
}

// ─── X Posting (Browser) ───

async function postToBrowserXPage(page, content, imagePath) {
  // Use the browser snapshot/act approach
  
  // Navigate to home
  await page.goto('https://x.com/home', { waitUntil: 'load' });
  await page.waitForTimeout(3000);
  
  // Check login
  const url = page.url();
  if (url.includes('/login') || url.includes('/i/flow/login')) {
    log('❌', 'X not logged in — need to login first');
    log('💡', 'Run: openclaw browser start && openclaw browser open https://x.com/login');
    log('💡', 'Then login manually, then: openclaw browser navigate https://x.com/home');
    return null;
  }
  
  // Find composer
  const composers = await page.$$('[data-testid="tweetTextarea_0"], [role="textbox"]');
  let composer = composers[0];
  
  if (!composer) {
    log('⚠️', 'Composer not found, clicking Post button');
    const postBtn = await page.$('a[href="/compose/post"], [data-testid="SideNav_NewTweet_Button"]');
    if (postBtn) {
      await postBtn.click();
      await page.waitForTimeout(2000);
      composer = (await page.$$('[data-testid="tweetTextarea_0"], [role="textbox"]'))[0];
    }
  }
  
  if (!composer) {
    log('❌', 'Cannot find tweet composer');
    return null;
  }
  
  // Type content
  await composer.click();
  await page.waitForTimeout(300);
  await composer.fill(content);
  await page.waitForTimeout(500);
  
  // Upload image
  if (imagePath && fs.existsSync(imagePath)) {
    log('📸', 'Uploading image...');
    const fileInput = await page.$('input[type="file"]');
    if (fileInput) {
      await fileInput.setInputFiles(imagePath);
      await page.waitForTimeout(2000);
    } else {
      // Click media button first
      const mediaBtn = await page.$('[data-testid="toolBar"] [aria-label="Media"], button[aria-label="Add media"]');
      if (mediaBtn) {
        await mediaBtn.click();
        await page.waitForTimeout(1000);
        const input = await page.$('input[type="file"]');
        if (input) {
          await input.setInputFiles(imagePath);
          await page.waitForTimeout(2000);
        }
      }
    }
  }
  
  // Click Post
  const tweetBtn = await page.$('[data-testid="tweetButton"]');
  if (!tweetBtn) {
    log('❌', 'Cannot find Post button');
    return null;
  }
  await tweetBtn.click();
  await page.waitForTimeout(3000);
  
  // Get tweet URL from profile
  await page.goto('https://x.com/VotiveAstrology', { waitUntil: 'load' });
  await page.waitForTimeout(2000);
  
  const tweetLinks = await page.$$('a[href*="/status/"]');
  if (tweetLinks.length > 0) {
    const href = await tweetLinks[0].getAttribute('href');
    const url = `https://x.com${href}`;
    log('🐦', `Posted: ${url}`);
    return url;
  }
  
  log('⚠️', 'Tweet posted but URL not found');
  return 'https://x.com/VotiveAstrology (posted)';
}

// ─── Meta Posting (API) ───

async function postMeta(content, imagePath) {
  const token = fs.readFileSync(META_TOKEN_FILE, 'utf-8').trim();
  const PAGE_ID = '177281685466511';
  const IG_ID = '17841472353157389';
  const BASE = 'https://graph.facebook.com/v20.0';
  
  const results = { fb: null, ig: null };
  
  // ── Post to Facebook ──
  log('📘', 'Posting to Facebook Page...');
  
  let photoId = null;
  
  if (imagePath && fs.existsSync(imagePath)) {
    // Upload image via multipart
    const FormData = require('form-data');
    const form = new FormData();
    form.append('source', fs.createReadStream(imagePath));
    form.append('access_token', token);
    form.append('published', 'false');
    
    const uploadResult = await new Promise((resolve, reject) => {
      const req = https.request({
        hostname: 'graph.facebook.com',
        path: `/v20.0/${PAGE_ID}/photos`,
        method: 'POST',
        headers: form.getHeaders(),
      }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try { resolve(JSON.parse(data)); }
          catch { resolve(null); }
        });
      });
      req.on('error', reject);
      form.pipe(req);
    });
    
    if (uploadResult?.id) {
      photoId = uploadResult.id;
      log('📸', `Photo uploaded: ${photoId}`);
    } else {
      log('⚠️', `Photo upload failed: ${JSON.stringify(uploadResult)}`);
    }
  }
  
  // Create FB post
  const fbData = new URLSearchParams({ message: content, access_token: token });
  if (photoId) {
    fbData.append('attached_media', JSON.stringify({ media_fbid: photoId }));
  }
  
  const fbResult = await new Promise((resolve, reject) => {
    const req = https.request({
      hostname: 'graph.facebook.com',
      path: `/v20.0/${PAGE_ID}/feed`,
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { resolve(null); }
      });
    });
    req.on('error', reject);
    req.write(fbData.toString());
    req.end();
  });
  
  if (fbResult?.id) {
    results.fb = `https://facebook.com/${fbResult.id}`;
    log('✅', `Facebook posted: ${results.fb}`);
  } else {
    log('❌', `Facebook error: ${JSON.stringify(fbResult)}`);
  }
  
  // ── Post to Instagram ──
  if (imagePath && fs.existsSync(imagePath)) {
    log('📸', 'Posting to Instagram...');
    
    // Upload to FB first to get CDN URL
    const FormData = require('form-data');
    const form = new FormData();
    form.append('source', fs.createReadStream(imagePath));
    form.append('access_token', token);
    form.append('published', 'false');
    
    const uploadResult = await new Promise((resolve, reject) => {
      const req = https.request({
        hostname: 'graph.facebook.com',
        path: `/v20.0/${PAGE_ID}/photos`,
        method: 'POST',
        headers: form.getHeaders(),
      }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try { resolve(JSON.parse(data)); }
          catch { resolve(null); }
        });
      });
      req.on('error', reject);
      form.pipe(req);
    });
    
    if (uploadResult?.id) {
      // Get the CDN URL
      const photoInfo = await new Promise((resolve, reject) => {
        https.get(`https://graph.facebook.com/v20.0/${uploadResult.id}?fields=images&access_token=${token}`, (res) => {
          let data = '';
          res.on('data', chunk => data += chunk);
          res.on('end', () => {
            try { resolve(JSON.parse(data)); }
            catch { resolve(null); }
          });
        }).on('error', reject);
      });
      
      const imageUrl = photoInfo?.images?.[0]?.source;
      
      if (imageUrl) {
        // Create IG container
        const igContainer = await new Promise((resolve, reject) => {
          const igData = new URLSearchParams({
            image_url: imageUrl,
            caption: content.substring(0, 2000),
            access_token: token,
          });
          const req = https.request({
            hostname: 'graph.facebook.com',
            path: `/v20.0/${IG_ID}/media`,
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
              try { resolve(JSON.parse(data)); }
              catch { resolve(null); }
            });
          });
          req.on('error', reject);
          req.write(igData.toString());
          req.end();
        });
        
        if (igContainer?.id) {
          // Publish
          const igPublish = await new Promise((resolve, reject) => {
            const pubData = new URLSearchParams({
              creation_id: igContainer.id,
              access_token: token,
            });
            const req = https.request({
              hostname: 'graph.facebook.com',
              path: `/v20.0/${IG_ID}/media_publish`,
              method: 'POST',
              headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            }, (res) => {
              let data = '';
              res.on('data', chunk => data += chunk);
              res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch { resolve(null); }
              });
            });
            req.on('error', reject);
            req.write(pubData.toString());
            req.end();
          });
          
          if (igPublish?.id) {
            results.ig = `https://instagram.com/p/${igPublish.id}`;
            log('✅', `Instagram posted: ${results.ig}`);
          } else {
            log('❌', `IG publish error: ${JSON.stringify(igPublish)}`);
          }
        } else {
          log('❌', `IG container error: ${JSON.stringify(igContainer)}`);
        }
      } else {
        log('❌', 'Could not get CDN URL for image');
      }
    } else {
      log('❌', `IG image upload error: ${JSON.stringify(uploadResult)}`);
    }
  } else {
    log('⚠️', 'Instagram requires image — skipped');
  }
  
  return results;
}

// ─── Post Tracking ───

function loadPostsDB() {
  if (fs.existsSync(POSTS_DB)) {
    return JSON.parse(fs.readFileSync(POSTS_DB, 'utf-8'));
  }
  return { pipeline: 'vedic-astrology-weekly', posts: [], lastId: 0 };
}

function savePostsDB(db) {
  fs.writeFileSync(POSTS_DB, JSON.stringify(db, null, 2));
}

function getNextPostId(db) {
  const lastId = db.lastId || db.posts.length;
  const nextId = lastId + 1;
  return String(nextId).padStart(3, '0');
}

// ─── Main ───

async function main() {
  const args = process.argv.slice(2);
  const isDryRun = args.includes('--dry-run');
  const isHealth = args.includes('--health');
  
  console.log('╔══════════════════════════════════════════════╗');
  console.log('║   🪐 Vedic Weekly Pipeline v2               ║');
  console.log('╚══════════════════════════════════════════════╝');
  
  if (isHealth) {
    log('🔍', 'Auth Health Check:');
    checkXSession();
    await checkMetaToken();
    return;
  }
  
  // ── Auth check ──
  log('🔍', 'Checking auth status...');
  const hasXSession = checkXSession();
  const hasMeta = await checkMetaToken();
  
  if (!hasXSession) {
    log('⚠️', 'X posting: browser session needed');
    log('   ', 'Run with --login-x to save session');
  }
  
  if (!hasMeta) {
    log('⚠️', 'Meta posting: new token needed');
    log('   ', 'Refresh at: https://developers.facebook.com/tools/explorer/');
    log('   ', 'Save to:', META_TOKEN_FILE);
  }
  
  if (isDryRun) {
    log('🏁', 'Dry run complete');
    return;
  }
  
  // ── Load content ──
  let xContentFile, metaContentFile, imageFile;
  
  const contentIdx = args.indexOf('--post');
  if (contentIdx >= 0) {
    xContentFile = args[contentIdx + 1];
    metaContentFile = args[contentIdx + 2];
    imageFile = args[contentIdx + 3];
  } else {
    // Auto-detect latest unposted content
    const db = loadPostsDB();
    const nextId = getNextPostId(db);
    xContentFile = path.join(ROOT, `vedic-post-${nextId}-x.md`);
    metaContentFile = path.join(ROOT, `vedic-post-${nextId}-meta.md`);
    imageFile = path.join(ROOT, `vedic-post-${nextId}.jpg`);
    
    // Check if they exist
    if (!fs.existsSync(xContentFile)) {
      log('❌', `Content not found: ${xContentFile}`);
      log('💡', 'Create content first, then run with --post flag');
      process.exit(1);
    }
  }
  
  if (!fs.existsSync(xContentFile)) {
    log('❌', `X content not found: ${xContentFile}`);
    process.exit(1);
  }
  if (!fs.existsSync(metaContentFile)) {
    log('❌', `Meta content not found: ${metaContentFile}`);
    process.exit(1);
  }
  
  const xContent = fs.readFileSync(xContentFile, 'utf-8').trim();
  const metaContent = fs.readFileSync(metaContentFile, 'utf-8').trim();
  const hasImage = imageFile && fs.existsSync(imageFile);
  
  const postId = path.basename(xContentFile).match(/vedic-post-(\d+)/)?.[1] || '???';
  
  log('📄', `Post #${postId}`);
  log('   ', `X content: ${xContent.length} chars`);
  log('   ', `Meta content: ${metaContent.length} chars`);
  log('   ', `Image: ${hasImage ? '✅' : '❌'}`);
  
  const results = { x_url: null, fb_url: null, ig_url: null };
  
  // ── Post to X ──
  if (!hasXSession) {
    log('⏭️', 'Skipping X post (no auth)');
  } else {
    log('🐦', 'Posting to X...');
    // The X posting via browser requires Playwright
    // For cron, we let the x_poster.js handle it
    try {
      const args = ['--content', xContentFile];
      if (fs.existsSync(imageFile)) args.push('--image', imageFile);
      
      execSync(`node "${path.join(ROOT, 'x_poster.js')}" ${args.join(' ')}`, {
        cwd: ROOT,
        stdio: 'pipe',
        timeout: 60000,
      });
      // Note: URL extraction from x_poster.js output would need parsing
      log('✅', 'X post attempted (check x_poster.js output)');
    } catch (e) {
      log('❌', `X post failed: ${e.message}`);
      log('💡', 'Run x_poster.js manually to debug');
    }
  }
  
  // ── Post to Meta ──
  if (!hasMeta) {
    log('⏭️', 'Skipping Meta post (no auth)');
  } else {
    log('📘', 'Posting to Meta...');
    try {
      // Use meta_post.py for FB
      const fbArgs = ['fb', `"${metaContent}"`];
      if (fs.existsSync(imageFile)) {
        // meta_post.py needs the image path for local upload
        // For now, use the script with image_path
        execSync(`python3 "${path.join(META_PIPELINE, 'meta_post.py')}" fb "${metaContent}"`, {
          cwd: META_PIPELINE,
          stdio: 'pipe',
          timeout: 60000,
        });
      }
      
      // For IG, upload via API
      execSync(`python3 "${path.join(META_PIPELINE, 'meta_post.py')}" ig-photo "" "${metaContent.substring(0, 2000)}"`, {
        cwd: META_PIPELINE, 
        stdio: 'pipe',
        timeout: 60000,
      });
      log('✅', 'Meta posts attempted');
    } catch (e) {
      log('❌', `Meta post failed: ${e.message}`);
    }
  }
  
  // ── Record in DB ──
  const db = loadPostsDB();
  db.posts.push({
    id: postId,
    date: new Date().toISOString().split('T')[0],
    type: 'planetary_transit',
    title: xContent.split('\n')[0].replace(/^[🪐🌟✨#]*\s*/, '').substring(0, 80),
    x_url: results.x_url || null,
    meta: results.fb_url ? 'published' : 'failed',
    content_file: `vedic-post-${postId}-x.md`,
    meta_file: `vedic-post-${postId}-meta.md`,
    image: `vedic-post-${postId}.jpg`,
    status: (results.x_url || results.fb_url) ? 'published' : 'failed',
  });
  db.lastId = parseInt(postId);
  savePostsDB(db);
  
  // ── Summary ──
  console.log('\n╔══════════════════════════════════════════╗');
  console.log('║           📊 Post Summary                ║');
  console.log('╚══════════════════════════════════════════╝');
  console.log(`  📄 Post #${postId}`);
  console.log(`  🐦 X:     ${results.x_url || '❌ failed'}`);
  console.log(`  📘 FB:    ${results.fb_url || '❌ failed'}`);
  console.log(`  📸 IG:    ${results.ig_url || '❌ failed'}`);
  console.log('');
  
  return results;
}

main().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
