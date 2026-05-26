#!/usr/bin/env node
/**
 * YouTube KPI Tracker — Pull channel stats & log to kpi_tracker.json
 * Usage: node kpi_check.js
 */

const fs = require('fs');
const path = require('path');
const { google } = require('googleapis');
const { OAuth2Client } = require('google-auth-library');

const CREDENTIALS_PATH = path.join(__dirname, 'oauth-credentials.json');
const TOKEN_PATH = path.join(__dirname, 'oauth-tokens.json');
const KPI_PATH = path.join(__dirname, 'kpi_tracker.json');
const CHANNEL_ID = 'UCRQTGFyWaXFUOx-2u61SPTw';

async function main() {
    const creds = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf-8'));
    const token = JSON.parse(fs.readFileSync(TOKEN_PATH, 'utf-8'));
    
    const oauth = new OAuth2Client(creds.installed.client_id, creds.installed.client_secret, creds.installed.redirect_uris[0]);
    oauth.setCredentials(token);
    
    if (token.expiry_date && token.expiry_date < Date.now() + 60000) {
        const { credentials } = await oauth.refreshAccessToken();
        oauth.setCredentials(credentials);
        fs.writeFileSync(TOKEN_PATH, JSON.stringify(oauth.credentials, null, 2));
    }
    
    const youtube = google.youtube({ version: 'v3', auth: oauth });
    
    // Channel stats
    const ch = await youtube.channels.list({
        part: ['statistics'],
        id: [CHANNEL_ID]
    });
    const stats = ch.data.items[0].statistics;
    
    // All video stats
    const search = await youtube.search.list({
        part: ['id'],
        channelId: CHANNEL_ID,
        maxResults: 50,
        order: 'date',
        type: 'video'
    });
    
    const videoIds = search.data.items.map(v => v.id.videoId);
    let totalViews = 0, totalLikes = 0, totalComments = 0;
    
    if (videoIds.length > 0) {
        const vStats = await youtube.videos.list({
            part: ['statistics', 'snippet'],
            id: [videoIds.join(',')]
        });
        
        for (const v of vStats.data.items) {
            totalViews += parseInt(v.statistics.viewCount || 0);
            totalLikes += parseInt(v.statistics.likeCount || 0);
            totalComments += parseInt(v.statistics.commentCount || 0);
        }
    }
    
    const result = {
        date: new Date().toISOString().split('T')[0],
        time: new Date().toISOString().split('T')[1].slice(0, 8),
        subscribers: parseInt(stats.subscriberCount || 0),
        totalViews,
        totalLikes,
        totalComments,
        videoCount: parseInt(stats.videoCount || 0),
        avgViewsPerVideo: videoIds.length > 0 ? Math.round(totalViews / videoIds.length) : 0
    };
    
    // Update KPI tracker
    const kpi = JSON.parse(fs.readFileSync(KPI_PATH, 'utf-8'));
    kpi.weeklyResults.push(result);
    fs.writeFileSync(KPI_PATH, JSON.stringify(kpi, null, 2));
    
    console.log(JSON.stringify(result, null, 2));
    
    // Compare to targets
    const now = new Date(result.date);
    let currentTarget = null;
    for (const [week, target] of Object.entries(kpi.targets)) {
        if (new Date(target.endDate) >= now) {
            currentTarget = { week, ...target };
            break;
        }
    }
    
    if (currentTarget) {
        console.log(`\n📊 vs ${currentTarget.week} Target:`);
        console.log(`   Subscribers: ${result.subscribers}/${currentTarget.subscribers} (${(result.subscribers/currentTarget.subscribers*100).toFixed(0)}%)`);
        console.log(`   Avg Views:   ${result.avgViewsPerVideo}/${currentTarget.avgViewsPerVideo} (${(result.avgViewsPerVideo/currentTarget.avgViewsPerVideo*100).toFixed(0)}%)`);
        console.log(`   Total Views: ${result.totalViews}/${currentTarget.cumulativeViews} (${(result.totalViews/currentTarget.cumulativeViews*100).toFixed(0)}%)`);
    }
}

main().catch(e => { console.error(e.message); process.exit(1); });
