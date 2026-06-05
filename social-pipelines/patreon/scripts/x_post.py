#!/usr/bin/env python3
"""
X (Twitter) API v2 Auto Poster
Usage:
  python3 x_post.py "message"
  python3 x_post.py "message" /path/to/image.jpg
"""

import tweepy
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return tweepy.Client(
        consumer_key=os.environ.get("X_API_KEY"),
        consumer_secret=os.environ.get("X_API_SECRET"),
        access_token=os.environ.get("X_ACCESS_TOKEN"),
        access_token_secret=os.environ.get("X_ACCESS_SECRET"),
    )

def get_v1_api():
    """tweepy v1 API for media upload"""
    auth = tweepy.OAuth1UserHandler(
        os.environ.get("X_API_KEY"),
        os.environ.get("X_API_SECRET"),
        os.environ.get("X_ACCESS_TOKEN"),
        os.environ.get("X_ACCESS_SECRET"),
    )
    return tweepy.API(auth)

def post_tweet(text, image_path=None):
    client = get_client()
    v1 = get_v1_api()
    
    media_id = None
    
    if image_path and os.path.exists(image_path):
        print(f"📸 Uploading image: {image_path}")
        media_id = v1.media_upload(image_path).media_id
        print(f"   Media ID: {media_id}")
    
    print(f"📝 Posting tweet ({len(text)} chars)...")
    resp = client.create_tweet(text=text, media_ids=[media_id] if media_id else None)
    
    if "data" in resp.data:
        tweet_id = resp.data["id"]
        print(f"✅ Tweet posted: https://x.com/VotiveAstrology/status/{tweet_id}")
        return tweet_id
    else:
        print(f"❌ Error: {resp.data}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 x_post.py 'message' [image_path]")
        sys.exit(1)
    
    text = sys.argv[1]
    image_path = sys.argv[2] if len(sys.argv) > 2 else None
    post_tweet(text, image_path)
