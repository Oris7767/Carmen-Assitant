#!/usr/bin/env node
/**
 * One-time OAuth setup — starts local server to capture redirect.
 * Run: node youtube_auth.js
 * Then open the printed URL in browser.
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const { google } = require('googleapis');
const { OAuth2Client } = require('google-auth-library');

const CREDENTIALS_PATH = path.join(__dirname, 'oauth-credentials.json');
const TOKEN_PATH = path.join(__dirname, 'oauth-tokens.json');
const PORT = 8080;

const SCOPES = [
  'https://www.googleapis.com/auth/youtube.upload',
  'https://www.googleapis.com/auth/youtube',
];

async function main() {
  const creds = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf-8'));
  const { client_id, client_secret, redirect_uris } = creds.installed;
  const oauth = new OAuth2Client(client_id, client_secret, `http://localhost:${PORT}`);

  const authUrl = oauth.generateAuthUrl({
    access_type: 'offline',
    scope: SCOPES,
    prompt: 'consent',
  });

  console.log('\n🔐 Open this URL in your browser:\n');
  console.log(authUrl);
  console.log('\n⏳ Waiting for authorization...\n');

  // Start local HTTP server to receive the redirect
  const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);

    if (url.pathname === '/' && url.searchParams.has('code')) {
      const code = url.searchParams.get('code');

      try {
        const { tokens } = await oauth.getToken(code);
        oauth.setCredentials(tokens);
        fs.writeFileSync(TOKEN_PATH, JSON.stringify(tokens, null, 2));

        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end('<h2>✅ Authorization successful!</h2><p>You may close this window.</p>');
        console.log('✅ Refresh token saved!');
      } catch (e) {
        res.writeHead(500);
        res.end('Error: ' + e.message);
        console.error('❌ Error exchanging code:', e.message);
      }

      server.close();
      process.exit(0);
    } else if (url.pathname === '/' && url.searchParams.has('error')) {
      res.writeHead(400, { 'Content-Type': 'text/html' });
      res.end(`<h2>❌ Authorization denied</h2><p>${url.searchParams.get('error')}</p>`);
      server.close();
      process.exit(1);
    } else {
      res.writeHead(404);
      res.end('Not found');
    }
  });

  server.listen(PORT, () => {
    console.log(`📡 Listening on http://localhost:${PORT}\n`);
  });

  // Timeout after 5 minutes
  setTimeout(() => {
    console.log('\n⏰ Timeout — no authorization received.');
    server.close();
    process.exit(1);
  }, 300000);
}

main().catch(e => { console.error(e); process.exit(1); });
