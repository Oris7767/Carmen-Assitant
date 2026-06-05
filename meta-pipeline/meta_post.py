"""
Meta Pipeline — Post to Facebook Page & Instagram
=================================================
Usage:
  python3 meta_post.py fb "Hello World"
  python3 meta_post.py ig-photo https://example.com/image.jpg "Caption here"
  python3 meta_post.py ig-video https://example.com/reel.mp4 "Caption here"
"""

import requests
import json
import sys
import os

# Config
PAGE_ID = "177281685466511"
PAGE_NAME = "Votive Academy"
IG_ID = "17841472353157389"
IG_USERNAME = "votive_edu"
VERSION = "v20.0"

# Load token from env or file
def get_token():
    token = os.environ.get("META_PAGE_TOKEN")
    if not token:
        token_file = os.path.join(os.path.dirname(__file__), ".token")
        if os.path.exists(token_file):
            with open(token_file, "r") as f:
                token = f.read().strip()
    return token

BASE = f"https://graph.facebook.com/{VERSION}"

def post_fb(text, image_url=None, image_path=None, video_url=None, scheduled_time=None):
    """Post to Facebook Page
    
    Args:
        text: Post message
        image_url: Public URL of image
        image_path: Local file path (upload via multipart)
        video_url: Public URL of video
        scheduled_time: datetime for scheduled post
    """
    token = get_token()
    url = f"{BASE}/{PAGE_ID}/feed"
    
    data = {"message": text, "access_token": token}
    
    photo_id = None
    
    if image_path and not image_url:
        # Upload local file via multipart
        import os
        img_url_fb = f"{BASE}/{PAGE_ID}/photos"
        with open(image_path, 'rb') as f:
            files = {'source': (os.path.basename(image_path), f, 'image/jpeg')}
            img_data = {'access_token': token, 'published': 'false'}
            resp = requests.post(img_url_fb, data=img_data, files=files)
        result = resp.json()
        if "id" in result:
            photo_id = result["id"]
            print(f"📸 Photo uploaded: {photo_id}")
        else:
            print(f"⚠️ FB photo upload error (file): {result}")
    
    if image_url:
        # Upload image via URL
        img_url = f"{BASE}/{PAGE_ID}/photos"
        img_data = {"url": image_url, "published": "false", "access_token": token}
        resp = requests.post(img_url, data=img_data)
        result = resp.json()
        if "id" in result:
            photo_id = result["id"]
            print(f"📸 Photo uploaded (URL): {photo_id}")
    
    # Fix: use multipart for attached_media to avoid JSON escape issues
    if photo_id:
        data["attached_media"] = f'[{json.dumps({"media_fbid": photo_id})}]'
    
    if video_url:
        url = f"{BASE}/{PAGE_ID}/videos"
        data["file_url"] = video_url
        data["title"] = text[:100]
    
    if scheduled_time:
        data["scheduled_publish_time"] = int(scheduled_time.timestamp())
        data["published"] = "false"
    
    # FIX: Force multipart/form-data encoding for attached_media
    # Facebook Graph API requires multipart for attached_media to parse correctly
    if photo_id:
        # Use a dummy file to force multipart encoding
        resp = requests.post(url, data=data, files={'upload': ('', '', 'application/octet-stream')})
    else:
        resp = requests.post(url, data=data)
    result = resp.json()
    
    if "id" in result:
        print(f"✅ Facebook post created: {result['id']}")
        return result["id"]
    else:
        print(f"❌ Facebook error: {result}")
        return None

def post_ig_photo(image_url=None, image_path=None, caption=""):
    """Post single image to Instagram
    
    Args:
        image_url: Public URL of the image
        image_path: Local file path (will upload via multipart to FB first)
        caption: Image caption
    """
    token = get_token()
    
    # If local file, upload to FB first to get a hosted URL
    if image_path and not image_url:
        import os
        if not os.path.exists(image_path):
            print(f"❌ File not found: {image_path}")
            return None
        
        # Upload photo to Facebook Page to get a hosted URL
        fb_photo_url = f"{BASE}/{PAGE_ID}/photos"
        with open(image_path, 'rb') as f:
            files = {'source': (os.path.basename(image_path), f, 'image/jpeg')}
            fb_data = {'access_token': token, 'published': 'false'}
            resp = requests.post(fb_photo_url, data=fb_data, files=files)
        result = resp.json()
        
        if "id" not in result:
            print(f"❌ FB photo upload error: {result}")
            return None
        
        fb_photo_id = result["id"]
        print(f"📸 FB photo uploaded: {fb_photo_id}")
        
        # Get the hosted URL of the uploaded photo
        photo_url = f"{BASE}/{fb_photo_id}?fields=images&access_token={token}"
        resp = requests.get(photo_url.split('?')[0], params={'fields': 'images', 'access_token': token})
        result = resp.json()
        
        if "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0]["source"]
            print(f"🔗 Image URL: {image_url}")
        else:
            # Fallback: use temporary FB photo URL
            image_url = f"https://graph.facebook.com/{VERSION}/{fb_photo_id}/picture?access_token={token}"
    
    if not image_url:
        print("❌ No image URL or path provided")
        return None
    
    # Step 1: Create media container
    url = f"{BASE}/{IG_ID}/media"
    data = {
        "image_url": image_url,
        "caption": caption,
        "access_token": token
    }
    resp = requests.post(url, data=data)
    result = resp.json()
    
    if "id" not in result:
        print(f"❌ IG create error: {result}")
        return None
    
    container_id = result["id"]
    print(f"📦 IG container created: {container_id}")
    
    # Step 2: Publish
    publish_url = f"{BASE}/{IG_ID}/media_publish"
    pub_data = {
        "creation_id": container_id,
        "access_token": token
    }
    resp = requests.post(publish_url, data=pub_data)
    result = resp.json()
    
    if "id" in result:
        print(f"✅ IG post published: {result['id']}")
        return result["id"]
    else:
        print(f"❌ IG publish error: {result}")
        return None

def post_ig_video(video_url, caption, media_type="REELS"):
    """Post video/reel to Instagram"""
    token = get_token()
    
    url = f"{BASE}/{IG_ID}/media"
    data = {
        "media_type": media_type,
        "video_url": video_url,
        "caption": caption,
        "access_token": token
    }
    resp = requests.post(url, data=data)
    result = resp.json()
    
    if "id" not in result:
        print(f"❌ IG create error: {result}")
        return None
    
    container_id = result["id"]
    print(f"📦 IG video container created: {container_id}")
    
    # Publish
    publish_url = f"{BASE}/{IG_ID}/media_publish"
    pub_data = {
        "creation_id": container_id,
        "access_token": token
    }
    resp = requests.post(publish_url, data=pub_data)
    result = resp.json()
    
    if "id" in result:
        print(f"✅ IG {media_type} published: {result['id']}")
        return result["id"]
    else:
        print(f"❌ IG publish error: {result}")
        return None

def post_ig_carousel(image_urls, caption):
    """Post carousel (multiple images) to Instagram"""
    token = get_token()
    child_ids = []
    
    # Upload each child image
    for img_url in image_urls:
        url = f"{BASE}/{IG_ID}/media"
        data = {
            "image_url": img_url,
            "is_carousel_item": "true",
            "access_token": token
        }
        resp = requests.post(url, data=data)
        result = resp.json()
        if "id" in result:
            child_ids.append(result["id"])
            print(f"📦 IG child uploaded: {result['id']}")
        else:
            print(f"❌ IG child upload error: {result}")
            return None
    
    # Create carousel container
    url = f"{BASE}/{IG_ID}/media"
    data = {
        "media_type": "CAROUSEL",
        "children": ",".join(child_ids),
        "caption": caption,
        "access_token": token
    }
    resp = requests.post(url, data=data)
    result = resp.json()
    
    if "id" not in result:
        print(f"❌ IG carousel create error: {result}")
        return None
    
    container_id = result["id"]
    
    # Publish
    publish_url = f"{BASE}/{IG_ID}/media_publish"
    pub_data = {
        "creation_id": container_id,
        "access_token": token
    }
    resp = requests.post(publish_url, data=pub_data)
    result = resp.json()
    
    if "id" in result:
        print(f"✅ IG carousel published: {result['id']}")
        return result["id"]
    else:
        print(f"❌ IG publish error: {result}")
        return None

def check_status(media_id):
    """Check post status"""
    token = get_token()
    url = f"{BASE}/{media_id}?fields=status_code,access_token&access_token={token}"
    resp = requests.get(url)
    return resp.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 meta_post.py fb 'message' [image_url]")
        print("  python3 meta_post.py ig-photo 'image_url' 'caption'")
        print("  python3 meta_post.py ig-video 'video_url' 'caption'")
        print("  python3 meta_post.py ig-carousel 'url1,url2' 'caption'")
        sys.exit(1)
    
    platform = sys.argv[1].lower()
    
    if platform == "fb":
        if len(sys.argv) < 3:
            print("Usage: python3 meta_post.py fb 'message' [image_url]")
            sys.exit(1)
        text = sys.argv[2]
        image_url = sys.argv[3] if len(sys.argv) > 3 else None
        post_fb(text, image_url)
        
    elif platform == "ig-photo":
        if len(sys.argv) < 4:
            print("Usage: python3 meta_post.py ig-photo 'image_url' 'caption'")
            sys.exit(1)
        post_ig_photo(sys.argv[2], sys.argv[3])
        
    elif platform == "ig-video":
        if len(sys.argv) < 4:
            print("Usage: python3 meta_post.py ig-video 'video_url' 'caption'")
            sys.exit(1)
        post_ig_video(sys.argv[2], sys.argv[3])
        
    elif platform == "ig-carousel":
        if len(sys.argv) < 4:
            print("Usage: python3 meta_post.py ig-carousel 'url1,url2' 'caption'")
            sys.exit(1)
        urls = sys.argv[2].split(",")
        post_ig_carousel(urls, sys.argv[3])
        
    else:
        print(f"Unknown platform: {platform}")
        sys.exit(1)
