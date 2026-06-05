const { TwitterApi } = require('twitter-api-v2');
require('dotenv').config();

async function testXAPI() {
  console.log('=== X (Twitter) API v2 Test ===\n');
  
  // 1. Check credentials
  console.log('[1] Credentials check:');
  console.log('  X_API_KEY:', process.env.X_API_KEY ? '✅ set' : '❌ MISSING');
  console.log('  X_API_SECRET:', process.env.X_API_SECRET ? '✅ set' : '❌ MISSING');
  console.log('  X_ACCESS_TOKEN:', process.env.X_ACCESS_TOKEN ? '✅ set' : '❌ MISSING');
  console.log('  X_ACCESS_SECRET:', process.env.X_ACCESS_SECRET ? '✅ set' : '❌ MISSING');
  console.log('  X_BEARER_TOKEN:', process.env.X_BEARER_TOKEN ? '✅ set' : '⚠️  EMPTY');
  
  const client = new TwitterApi({
    appKey: process.env.X_API_KEY,
    appSecret: process.env.X_API_SECRET,
    accessToken: process.env.X_ACCESS_TOKEN,
    accessSecret: process.env.X_ACCESS_SECRET,
  });
  
  const rwClient = client.readWrite;
  
  // 2. Test me() - user info
  console.log('\n[2] Testing me() endpoint...');
  try {
    const me = await rwClient.v2.me();
    console.log('  ✅ SUCCESS - Authenticated');
    console.log('  ID:', me.data.id);
    console.log('  Name:', me.data.name);
    console.log('  Username:', me.data.username);
  } catch (err) {
    console.log('  ❌ FAILED');
    console.log('  Error code:', err.code);
    console.log('  Error message:', err.data?.detail || err.message);
    console.log('  Full error:', JSON.stringify(err.data || err, null, 2).slice(0, 500));
  }
  
  // 3. Test tweet lookup (public)
  console.log('\n[3] Testing tweet lookup...');
  try {
    const tweet = await rwClient.v2.singleTweet('2058227660082598253');
    console.log('  ✅ SUCCESS - Can read tweets');
    console.log('  Text:', tweet.data.text.slice(0, 100) + '...');
  } catch (err) {
    console.log('  ❌ FAILED:', err.data?.detail || err.message);
  }
  
  // 4. Test user timeline
  console.log('\n[4] Testing user timeline (VotiveAstrology)...');
  try {
    const meData = await rwClient.v2.me();
    const timeline = await rwClient.v2.userTimeline(meData.data.id, { max_results: 5 });
    console.log('  ✅ SUCCESS - Timeline accessible');
    console.log('  Recent tweets:', timeline.data?.meta?.result_count || timeline.tweets?.length || 'N/A');
    if (timeline.data?.data?.length) {
      timeline.data.data.forEach((t, i) => {
        console.log(`    [${i+1}] ${t.text.slice(0, 80)}...`);
      });
    }
  } catch (err) {
    console.log('  ❌ FAILED:', err.data?.detail || err.message);
  }
  
  // 5. Rate limit check
  console.log('\n[5] Rate limit info...');
  try {
    const meData = await rwClient.v2.me();
    console.log('  Rate limit remaining:', meData.rateLimit?.remaining || 'N/A');
    console.log('  Rate limit reset:', meData.rateLimit?.reset ? new Date(meData.rateLimit.reset * 1000).toISOString() : 'N/A');
  } catch (err) {
    console.log('  ❌ FAILED:', err.message);
  }
  
  console.log('\n=== Test Complete ===');
}

testXAPI().catch(console.error);
