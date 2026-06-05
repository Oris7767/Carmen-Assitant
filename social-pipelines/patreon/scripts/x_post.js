#!/usr/bin/env node
/**
 * X (Twitter) API v2 Auto Poster
 * Usage:
 *   node x_post.js "message"
 *   node x_post.js "message" /path/to/image.jpg
 */

const { TwitterApi } = require('twitter-api-v2');
require('dotenv').config();

const client = new TwitterApi({
  appKey: process.env.X_API_KEY,
  appSecret: process.env.X_API_SECRET,
  accessToken: process.env.X_ACCESS_TOKEN,
  accessSecret: process.env.X_ACCESS_SECRET,
});

const rw = client.readWrite;

async function postTweet(text, imagePath) {
  console.log('🐦 X API v2 Auto Poster');
  console.log(`   Text: ${text.length} chars`);
  console.log(`   Image: ${imagePath || 'none'}`);

  try {
    let mediaId = null;

    if (imagePath) {
      console.log('📸 Uploading image...');
      const media = await rw.v1.uploadMedia(imagePath);
      mediaId = media.media_id_string;
      console.log(`   Media ID: ${mediaId}`);
    }

    console.log('📝 Posting tweet...');
    const tweetParams = { text };
    if (mediaId) {
      tweetParams.media = { media_ids: [mediaId] };
    }

    const tweet = await rw.v2.tweet(tweetParams);
    const tweetId = tweet.data.id;
    console.log(`✅ Tweet posted!`);
    console.log(`   https://x.com/VotiveAstrology/status/${tweetId}`);
    return tweetId;
  } catch (err) {
    console.error(`❌ Error: ${err.message}`);
    if (err.data) {
      console.error(`   Detail: ${JSON.stringify(err.data).slice(0, 500)}`);
    }
    process.exit(1);
  }
}

// Parse args
const args = process.argv.slice(2);
if (args.length < 1) {
  console.log('Usage: node x_post.js "message" [image_path]');
  process.exit(1);
}

const text = args[0];
const imagePath = args[1] || null;

postTweet(text, imagePath);
