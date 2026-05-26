#!/usr/bin/env node
/**
 * YouTube API Uploader — OAuth 2.0 + YouTube Data API v3
 *
 * Usage:
 *   node youtube_api.js <video.mp4> <title> [description] [privacy]
 *
 * Examples:
 *   node youtube_api.js output_001.mp4 "Mặt Trăng gặp Ketu | 23.05" "desc" unlisted
 *   node youtube_api.js output_001.mp4 "Title" "" public
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { google } = require('googleapis');
const { OAuth2Client } = require('google-auth-library');

// ── Config ──────────────────────────────────────────────────
const CREDENTIALS_PATH = path.join(__dirname, 'oauth-credentials.json');
const TOKEN_PATH = path.join(__dirname, 'oauth-tokens.json');
const CSV_PATH = path.join(__dirname, 'video_log.csv');
const SCOPES = [
  'https://www.googleapis.com/auth/youtube.upload',
  'https://www.googleapis.com/auth/youtube',
];
const CHANNEL_ID = 'UCRQTGFyWaXFUOx-2u61SPTw';

function log(msg) {
  console.log(`[YT-API] ${new Date().toISOString().slice(11, 19)} ${msg}`);
}

// ── Auth ────────────────────────────────────────────────────
async function getOAuthClient() {
  const content = fs.readFileSync(CREDENTIALS_PATH, 'utf-8');
  const credentials = JSON.parse(content);
  const { client_id, client_secret, redirect_uris } = credentials.installed;

  const oauth = new OAuth2Client(client_id, client_secret, redirect_uris[0]);

  // Try to load saved token
  if (fs.existsSync(TOKEN_PATH)) {
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'));
    oauth.setCredentials(token);

    // Refresh if expired
    oauth.on('tokens', (tokens) => {
      if (tokens.refresh_token) {
        token.refresh_token = tokens.refresh_token;
        fs.writeFileSync(TOKEN_PATH, JSON.stringify(token, null, 2));
        log('🔄 Refresh token updated');
      }
    });

    // Check if access token is expired
    if (token.expiry_date && token.expiry_date < Date.now() + 60000) {
      try {
        log('🔑 Refreshing access token...');
        const { credentials } = await oauth.refreshAccessToken();
        oauth.setCredentials(credentials);
        // Save refreshed token
        const updatedToken = oauth.credentials;
        fs.writeFileSync(TOKEN_PATH, JSON.stringify(updatedToken, null, 2));
      } catch (e) {
        log('⚠️  Refresh failed, re-authenticating...');
        fs.unlinkSync(TOKEN_PATH);
        return getOAuthClient();
      }
    }

    return oauth;
  }

  // ── First-time auth ──
  const authUrl = oauth.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent',
  });

  console.log('\n🔐 FIRST-TIME AUTH REQUIRED');
  console.log('─────────────────────────────────────');
  console.log('1. Open this URL in browser:\n');
  console.log(authUrl);
  console.log('\n2. Authorize the app');
  console.log('3. Copy the authorization code from the redirect URL');
  console.log('   (after redirect, look for ?code=... in the URL)\n');

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const code = await new Promise((resolve) => {
    rl.question('Enter authorization code: ', (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });

  const { tokens } = await oauth.getToken(code);
  oauth.setCredentials(tokens);
  fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2));
  log('✅ Tokens saved to oauth-tokens.json');

  return oauth;
}

// ── Upload Video ────────────────────────────────────────────
async function uploadVideo(auth, videoPath, options) {
  const youtube = google.youtube({ version: 'v3', auth });

  const fileSize = fs.statSync(videoPath).size;
  log(`📤 Uploading: ${path.basename(videoPath)} (${(fileSize / 1024 / 1024).toFixed(1)} MB)`);

  const res = await youtube.videos.insert({
    part: ['snippet', 'status'],
    notifySubscribers: false,
    requestBody: {
      snippet: {
        title: options.title,
        description: options.description || options.title,
        tags: options.tags || [],
        categoryId: '22',
      },
      status: {
        privacyStatus: options.privacy || 'unlisted',
        selfDeclaredMadeForKids: false,
      },
    },
    media: {
      body: fs.createReadStream(videoPath),
    },
  }, {
    onUploadProgress: (evt) => {
      const pct = ((evt.bytesRead / fileSize) * 100).toFixed(0);
      process.stdout.write(`\r  Upload: ${pct}%`);
    },
  });

  console.log('');
  const videoId = res.data.id;
  log(`✅ Uploaded! Video ID: ${videoId}`);
  log(`   URL: https://youtube.com/shorts/${videoId}`);

  return videoId;
}

// ── Set Thumbnail ───────────────────────────────────────────
async function setThumbnail(auth, videoId, thumbnailPath) {
  if (!thumbnailPath || !fs.existsSync(thumbnailPath)) {
    log('ℹ️  No thumbnail provided, skipping');
    return;
  }

  const youtube = google.youtube({ version: 'v3', auth });

  let stats = fs.statSync(thumbnailPath);
  let finalPath = thumbnailPath;
  const maxBytes = 2 * 1024 * 1024;

  if (stats.size > maxBytes) {
    log(`⚠️  Thumbnail too large (${(stats.size/1024/1024).toFixed(1)}MB), resizing...`);
    const resizedPath = thumbnailPath.replace(/\.png$/, '_thumb.png');
    const { execSync } = require('child_process');
    try {
      execSync(`sips -Z 720 "${thumbnailPath}" --out "${resizedPath}"`, { stdio: 'pipe' });
      stats = fs.statSync(resizedPath);
      if (stats.size > 0) {
        finalPath = resizedPath;
        log(`   Resized to ${(stats.size/1024).toFixed(0)}KB`);
      }
    } catch (e) {
      log(`⚠️  sips resize failed, will try original: ${e.message}`);
    }
  }

  log('🖼️  Setting thumbnail...');
  try {
    await youtube.thumbnails.set({
      videoId,
      media: {
        body: fs.createReadStream(finalPath),
      },
    });
    log('✅ Thumbnail set!');
  } catch (e) {
    if (e.code === 403) {
      log('⚠️  Thumbnail skipped — channel needs YouTube verification for custom thumbnails');
    } else {
      log(`⚠️  Thumbnail failed: ${e.message}`);
    }
  }

  if (finalPath !== thumbnailPath) {
    try { fs.unlinkSync(finalPath); } catch (e) {}
  }
}

// ── CSV Log ─────────────────────────────────────────────────
function csvLog(videoUrl, title, privacy) {
  const now = new Date();
  const line = [
    now.toISOString().slice(0, 10),
    now.toISOString().slice(11, 19),
    `"${title.replace(/"/g, '""')}"`,
    videoUrl,
    'short',
    `"published via API (${privacy})"`,
  ].join(',') + '\n';

  fs.appendFileSync(CSV_PATH, line);
  log('📋 CSV appended');
}

// ── Main ────────────────────────────────────────────────────
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log('Usage: node youtube_api.js <video.mp4> <title> [description] [privacy]');
    console.log('  privacy: public | unlisted (default) | private');
    process.exit(1);
  }

  const [videoPath, title, description, privacy] = args;
  const fullVideoPath = path.resolve(videoPath);

  if (!fs.existsSync(fullVideoPath)) {
    log(`❌ Video not found: ${fullVideoPath}`);
    process.exit(1);
  }

  log('🚀 YouTube API Uploader');
  log(`   Title: ${title}`);
  log(`   Privacy: ${privacy || 'unlisted'}`);

  const auth = await getOAuthClient();
  log('🔐 Authenticated');

  const videoId = await uploadVideo(auth, fullVideoPath, {
    title,
    description: description || '',
    privacy: privacy || 'unlisted',
  });

  const framesDir = path.join(__dirname, 'frames');
  if (fs.existsSync(framesDir)) {
    const frames = fs.readdirSync(framesDir).filter(f => f.endsWith('.png')).sort();
    if (frames.length > 0) {
      await setThumbnail(auth, videoId, path.join(framesDir, frames[0]));
    }
  }

  const videoUrl = `https://youtube.com/shorts/${videoId}`;
  csvLog(videoUrl, title, privacy || 'unlisted');

  console.log(`\n✅ DONE — ${videoUrl}`);
  process.exit(0);
}

main().catch((err) => {
  log(`❌ ${err.message}`);
  if (err.errors) err.errors.forEach(e => log(`   ${e.message}`));
  process.exit(1);
});
