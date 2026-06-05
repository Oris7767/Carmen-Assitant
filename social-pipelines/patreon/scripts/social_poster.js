#!/usr/bin/env node
/**
 * Carmen AI — Social Media Auto Poster
 * Posts promotional content to X (Twitter) and Instagram.
 * 
 * Usage:
 *   node social_poster.js --content ./x-post.md --image ./image.jpg --platform x
 *   node social_poster.js --content ./ig-post.md --image ./image.jpg --platform instagram
 *   node social_poster.js --content ./post.md --image ./image.jpg --platform both
 * 
 * Requires .env file with API keys (copy from .env and fill in)
 */

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { TwitterApi } = require('twitter-api-v2');

// ─────────────────── PARSE ARGS ───────────────────
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--content' && args[i + 1]) opts.contentPath = args[++i];
    else if (args[i] === '--image' && args[i + 1]) opts.imagePath = args[++i];
    else if (args[i] === '--platform' && args[i + 1]) opts.platform = args[++i];
  }
  if (!opts.platform) opts.platform = 'both';
  return opts;
}

function log(msg) { console.log(`[SocialBot] ${msg}`); }

// ─────────────────── X (TWITTER) POSTER ───────────────────
async function postToX(content, imagePath) {
  log('🐦 Posting to X...');

  const apiKey = process.env.X_API_KEY;
  const apiSecret = process.env.X_API_SECRET;
  const accessToken = process.env.X_ACCESS_TOKEN;
  const accessSecret = process.env.X_ACCESS_SECRET;

  if (!apiKey || !apiSecret || !accessToken || !accessSecret) {
    log('❌ Missing X API credentials in .env');
    log('   Cần đủ 4 key: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET');
    log('   Vào https://developer.twitter.com/en/portal/dashboard → App → Keys & Tokens');
    return { success: false, error: 'Missing X credentials' };
  }

  try {
    const client = new TwitterApi({
      appKey: apiKey,
      appSecret: apiSecret,
      accessToken: accessToken,
      accessSecret: accessSecret,
    });

    const rwClient = client.readWrite;
    const tweetText = content.trim();

    let mediaId = null;
    if (imagePath && fs.existsSync(imagePath)) {
      log('📸 Uploading image to X...');
      try {
        mediaId = await rwClient.v1.uploadMedia(imagePath, { mimeType: 'image/jpeg' });
        log(`   Media ID: ${mediaId}`);
      } catch (e) {
        log(`⚠️  Image upload failed: ${e.message} — posting text only`);
      }
    }

    // Try v2 first, fall back to v1.1 (doesn't require Project enrollment)
    let tweet;
    try {
      tweet = await rwClient.v2.tweet({
        text: tweetText,
        ...(mediaId && { media: { media_ids: [mediaId] } }),
      });
    } catch (v2Error) {
      if (v2Error.data?.reason === 'client-not-enrolled') {
        log('⚠️  v2 requires Project — falling back to v1.1 API');
        tweet = await rwClient.v1.tweet(tweetText, {
          ...(mediaId && { media_ids: mediaId }),
        });
      } else {
        throw v2Error;
      }
    }

    log(`✅ Posted to X! Tweet ID: ${tweet.data.id || tweet.id_str}`);
    log(`   URL: https://x.com/i/status/${tweet.data.id || tweet.id_str}`);
    return { success: true, id: tweet.data.id || tweet.id_str };

  } catch (error) {
    log(`❌ X post failed: ${error.message}`);
    if (error.data) log(`   API response: ${JSON.stringify(error.data)}`);
    return { success: false, error: error.message };
  }
}

// ─────────────────── INSTAGRAM POSTER ───────────────────
async function postToInstagram(content, imagePath) {
  log('📸 Posting to Instagram...');

  const accessToken = process.env.INSTAGRAM_ACCESS_TOKEN;
  const igAccountId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;

  if (!accessToken || !igAccountId) {
    log('❌ Missing Instagram credentials in .env');
    log('   Cần: INSTAGRAM_ACCESS_TOKEN + INSTAGRAM_BUSINESS_ACCOUNT_ID');
    return { success: false, error: 'Missing Instagram credentials' };
  }

  if (!imagePath || !fs.existsSync(imagePath)) {
    log('❌ Instagram yêu cầu phải có ảnh');
    return { success: false, error: 'No image provided' };
  }

  try {
    const https = require('https');
    const caption = content.trim();
    const imageData = fs.readFileSync(imagePath);
    const boundary = '----CarmenIG' + Date.now();

    // Build multipart form data
    const parts = [
      { name: 'image', filename: path.basename(imagePath), data: imageData, type: 'image/jpeg' },
      { name: 'caption', data: Buffer.from(caption) },
      { name: 'access_token', data: Buffer.from(accessToken) },
    ];

    const multipartBody = Buffer.concat(
      parts.flatMap(p => [
        Buffer.from(`--${boundary}\r\n`),
        p.filename
          ? Buffer.from(`Content-Disposition: form-data; name="${p.name}"; filename="${p.filename}"\r\nContent-Type: ${p.type}\r\n\r\n`)
          : Buffer.from(`Content-Disposition: form-data; name="${p.name}"\r\n\r\n`),
        p.data,
        Buffer.from('\r\n'),
      ]).concat(Buffer.from(`--${boundary}--\r\n`))
    );

    // Step 1: Create media container
    const createResult = await new Promise((resolve, reject) => {
      const req = https.request({
        hostname: 'graph.facebook.com',
        path: `/v18.0/${igAccountId}/media`,
        method: 'POST',
        headers: {
          'Content-Type': `multipart/form-data; boundary=${boundary}`,
          'Content-Length': multipartBody.length,
        },
      }, (res) => {
        let body = '';
        res.on('data', chunk => body += chunk);
        res.on('end', () => {
          try { resolve(JSON.parse(body)); }
          catch { resolve(null); }
        });
      });
      req.on('error', reject);
      req.write(multipartBody);
      req.end();
    });

    if (!createResult?.id) {
      log(`❌ Instagram media create failed: ${JSON.stringify(createResult)}`);
      return { success: false, error: createResult };
    }

    log(`📦 Media container: ${createResult.id}`);

    // Step 2: Publish
    const publishBody = new URLSearchParams({
      creation_id: createResult.id,
      access_token: accessToken,
    }).toString();

    const publishResult = await new Promise((resolve, reject) => {
      const req = https.request({
        hostname: 'graph.facebook.com',
        path: `/v18.0/${igAccountId}/media_publish`,
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Content-Length': Buffer.byteLength(publishBody),
        },
      }, (res) => {
        let body = '';
        res.on('data', chunk => body += chunk);
        res.on('end', () => {
          try { resolve(JSON.parse(body)); }
          catch { resolve(null); }
        });
      });
      req.on('error', reject);
      req.write(publishBody);
      req.end();
    });

    if (publishResult?.id) {
      log(`✅ Posted to Instagram! Media ID: ${publishResult.id}`);
      return { success: true, id: publishResult.id };
    } else {
      log(`❌ Instagram publish failed: ${JSON.stringify(publishResult)}`);
      return { success: false, error: publishResult };
    }

  } catch (error) {
    log(`❌ Instagram post failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

// ─────────────────── MAIN ───────────────────
async function main() {
  const opts = parseArgs();

  if (!opts.contentPath || !fs.existsSync(opts.contentPath)) {
    console.error('❌ --content must point to an existing file');
    process.exit(1);
  }

  const content = fs.readFileSync(opts.contentPath, 'utf-8');
  log(`📄 Content: ${opts.contentPath} (${content.length} chars)`);
  log(`🖼️  Image: ${opts.imagePath || '(none)'}`);
  log(`🎯 Platform: ${opts.platform}`);

  const results = {};

  if (opts.platform === 'x' || opts.platform === 'both') {
    results.x = await postToX(content, opts.imagePath);
  }

  if (opts.platform === 'instagram' || opts.platform === 'both') {
    results.instagram = await postToInstagram(content, opts.imagePath);
  }

  // Summary
  const xStatus = results.x?.success ? '✅' : results.x ? '❌' : '⊘';
  const igStatus = results.instagram?.success ? '✅' : results.instagram ? '❌' : '⊘';
  
  console.log(`\n📊 X: ${xStatus} | Instagram: ${igStatus}`);

  const anyFailed = (results.x && !results.x.success) || (results.instagram && !results.instagram.success);
  if (anyFailed) {
    log('⚠️  Một số nền tảng post thất bại — kiểm tra .env credentials');
    process.exit(1);
  }

  log('🎉 Done!');
}

main().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
