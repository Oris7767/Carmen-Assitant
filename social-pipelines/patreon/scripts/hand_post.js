#!/usr/bin/env node
/**
 * Carmen AI — Unified Hand-Post Pipeline
 * =======================================
 * Orchestrates posting to all platforms:
 *   1. Patreon (draft or publish)
 *   2. X/Twitter (browser)
 *   3. Meta: Facebook Page + Instagram (API)
 * 
 * Usage:
 *   node hand_post.js --content ./post.md [--image ./image.jpg] [--publish]
 * 
 * Flags:
 *   --content   Path to content file (required)
 *   --image     Path to image file (optional)
 *   --publish   Publish Patreon immediately (default: draft)
 *   --platform  Comma-separated: patreon,x,meta (default: all)
 *   --visible   Show browser for X posting
 */

const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const ROOT = __dirname; // patreon-db/
const META_PIPELINE = path.join(ROOT, '..', 'meta-pipeline');

// ─── Config ───
const CONFIG = {
  patreon: {
    poster: path.join(ROOT, 'patreon_poster.js'),
    publish: path.join(ROOT, 'patreon_publish.js'),
  },
  x: {
    poster: path.join(ROOT, 'x_poster.js'),
  },
  meta: {
    script: path.join(META_PIPELINE, 'meta_post.py'),
    token: path.join(META_PIPELINE, '.token'),
  },
  footer: `📩 votive@vedicvn.com
🌍 vedicvn.com
📞 +84 385448747`,
};

// ─── Helpers ───
function log(platform, msg, emoji = '📌') {
  const ts = new Date().toLocaleTimeString('vi-VN');
  console.log(`\n${emoji} [${platform}] ${ts} — ${msg}`);
}

function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    platforms: ['patreon', 'x', 'meta'],
    publish: false,
    visible: false,
  };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--content' && args[i + 1]) opts.contentPath = args[++i];
    else if (args[i] === '--image' && args[i + 1]) opts.imagePath = args[++i];
    else if (args[i] === '--publish') opts.publish = true;
    else if (args[i] === '--platform' && args[i + 1]) opts.platforms = args[++i].split(',').map(p => p.trim());
    else if (args[i] === '--visible') opts.visible = true;
  }
  return opts;
}

function runNode(file, args = []) {
  return new Promise((resolve, reject) => {
    const proc = spawn('node', [file, ...args], { stdio: 'inherit', cwd: ROOT });
    proc.on('close', code => {
      if (code === 0) resolve();
      else reject(new Error(`node ${file} exited with code ${code}`));
    });
    proc.on('error', reject);
  });
}

function runPython(file, args = [], env = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn('python3', [file, ...args], {
      stdio: 'inherit',
      cwd: META_PIPELINE,
      env: { ...process.env, ...env },
    });
    proc.on('close', code => {
      if (code === 0) resolve();
      else reject(new Error(`python3 ${file} exited with code ${code}`));
    });
    proc.on('error', reject);
  });
}

function truncateForIG(text, maxLen = 2000) {
  if (text.length <= maxLen) return text;
  // Truncate at word boundary
  let truncated = text.substring(0, maxLen);
  const lastSpace = truncated.lastIndexOf(' ');
  if (lastSpace > maxLen * 0.8) {
    truncated = truncated.substring(0, lastSpace);
  }
  return truncated + '...';
}

function addFooter(text) {
  return text.trim() + '\n\n' + CONFIG.footer;
}

// ─── Platform Handlers ───

async function postPatreon(opts) {
  log('Patreon', 'Starting...', '📖');
  
  // Step 1: Create draft
  const args = ['--content', opts.contentPath];
  if (opts.imagePath) args.push('--image', opts.imagePath);
  
  await runNode(CONFIG.patreon.poster, args);
  log('Patreon', 'Draft created ✅', '✅');
  
  // Step 2: Publish if requested
  if (opts.publish) {
    log('Patreon', 'Publishing...', '🚀');
    await runNode(CONFIG.patreon.publish);
    log('Patreon', 'Published ✅', '🎉');
  }
}

async function postX(opts) {
  log('X', 'Starting...', '🐦');
  
  const args = ['--content', opts.contentPath];
  if (opts.imagePath) args.push('--image', opts.imagePath);
  if (opts.visible) args.push('--visible');
  
  await runNode(CONFIG.x.poster, args);
  log('X', 'Posted ✅', '🎉');
}

async function postMeta(opts) {
  log('Meta', 'Starting...', '📸');
  
  // Read content
  let content = fs.readFileSync(opts.contentPath, 'utf-8');
  
  // Truncate for IG (max 2200, keep safe at 2000)
  const igContent = truncateForIG(content, 2000);
  
  // Add footer
  const fbContent = addFooter(content.trim());
  const igContentWithFooter = addFooter(igContent.trim());
  
  log('Meta', `FB content: ${fbContent.length} chars`);
  log('Meta', `IG content: ${igContentWithFooter.length} chars`);
  
  // Post to Facebook Page
  if (opts.imagePath && fs.existsSync(opts.imagePath)) {
    // Upload image to CDN first (Meta API needs public URL)
    log('Meta', 'Image upload requires public URL — posting text to FB, image to IG separately');
    
    // FB: text only (or use image URL if available)
    await runPython(CONFIG.meta.script, ['fb', fbContent]);
    log('Meta', 'Facebook Page posted ✅', '✅');
    
    // IG: image + caption
    if (opts.imagePath.startsWith('http')) {
      await runPython(CONFIG.meta.script, ['ig-photo', opts.imagePath, igContentWithFooter]);
    } else {
      // Local image — need to upload to CDN first
      log('Meta', '⚠️  Local image detected. IG needs public URL. Posting text-only to IG.', '⚠️');
      await runPython(CONFIG.meta.script, ['fb', igContentWithFooter]);
    }
    log('Meta', 'Instagram posted ✅', '✅');
  } else {
    // Text only — FB supports text, IG requires image/video
    await runPython(CONFIG.meta.script, ['fb', fbContent]);
    log('Meta', 'Facebook Page posted ✅', '✅');
    log('Meta', '⚠️  Instagram requires image/video — skipped (text-only post)', '⚠️');
  }
}

// ─── Main Pipeline ───

async function main() {
  const opts = parseArgs();
  
  console.log('╔══════════════════════════════════════════╗');
  console.log('║   🪐 Carmen AI — Hand-Post Pipeline     ║');
  console.log('╚══════════════════════════════════════════╝');
  
  if (!opts.contentPath || !fs.existsSync(opts.contentPath)) {
    console.error('❌ --content must point to an existing file');
    console.error('Usage: node hand_post.js --content ./post.md [--image ./image.jpg] [--publish] [--platform patreon,x,meta]');
    process.exit(1);
  }
  
  const content = fs.readFileSync(opts.contentPath, 'utf-8');
  console.log(`\n📄 Content: ${opts.contentPath} (${content.length} chars)`);
  console.log(`🖼️  Image: ${opts.imagePath || '(none)'}`);
  console.log(`📋 Platforms: ${opts.platforms.join(', ')}`);
  console.log(`📖 Patreon: ${opts.publish ? 'PUBLISH' : 'DRAFT'}`);
  
  const results = {};
  const startTime = Date.now();
  
  // Execute platforms in order
  for (const platform of opts.platforms) {
    const pStart = Date.now();
    try {
      switch (platform.trim().toLowerCase()) {
        case 'patreon':
          await postPatreon(opts);
          results.patreon = { status: 'ok', duration: Date.now() - pStart };
          break;
        case 'x':
        case 'twitter':
          await postX(opts);
          results.x = { status: 'ok', duration: Date.now() - pStart };
          break;
        case 'meta':
        case 'fb':
        case 'facebook':
        case 'ig':
        case 'instagram':
          await postMeta(opts);
          results.meta = { status: 'ok', duration: Date.now() - pStart };
          break;
        default:
          console.warn(`⚠️  Unknown platform: ${platform}`);
      }
    } catch (error) {
      console.error(`❌ ${platform} failed: ${error.message}`);
      results[platform] = { status: 'error', error: error.message, duration: Date.now() - pStart };
    }
  }
  
  // Summary
  const totalDuration = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log('\n╔══════════════════════════════════════════╗');
  console.log('║           📊 Pipeline Summary            ║');
  console.log('╚══════════════════════════════════════════╝');
  
  for (const [platform, result] of Object.entries(results)) {
    const icon = result.status === 'ok' ? '✅' : '❌';
    const duration = (result.duration / 1000).toFixed(1);
    console.log(`  ${icon} ${platform.padEnd(10)} ${duration}s`);
  }
  
  console.log(`\n  ⏱️  Total: ${totalDuration}s`);
  console.log('');
  
  // Check if any failed
  const failures = Object.entries(results).filter(([, r]) => r.status !== 'ok');
  if (failures.length > 0) {
    console.log('⚠️  Failures:');
    for (const [platform, result] of failures) {
      console.log(`   ❌ ${platform}: ${result.error}`);
    }
    process.exit(1);
  }
}

main().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
