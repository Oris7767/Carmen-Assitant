"""Quick script to get your Telegram chat ID from subscribers.json."""
import json, os

path = os.path.join(os.path.dirname(__file__), "subscribers.json")
try:
    with open(path) as f:
        data = json.load(f)
    subs = data.get("subscribers", [])
    if not subs:
        print("❌ No subscribers found.")
        print("→ Send /start to the Carmen bot first, then run again.")
    else:
        print("📋 Existing subscribers:")
        for s in subs:
            cid = s.get("chat_id")
            uname = s.get("username") or "(no username)"
            name = s.get("first_name") or "(no name)"
            print(f"  • Chat ID: {cid} — @{uname} ({name})")
except FileNotFoundError:
    print("❌ subscribers.json not found. Send /start to Carmen bot first.")
