"""
web.py — Carmen Telegram Bot + Flask Web Service for Render

Architecture:
- Flask (main process): /health, /broadcast, /subscribers, /webhook
- Telegram bot: Webhook mode (NO polling → NO 409 conflicts)
- UptimeRobot pings /health to keep Render awake
- Open to community — no authorization required, auto-broadcast only

Deployed on Render Web Service.
"""

from flask import Flask, jsonify, request
import os
import json
import pytz
import telebot
from telebot.types import Update

from run_bot import get_full_report_data
from report_generator import ReportGenerator

# ── App ──
app = Flask(__name__)

# ── Constants ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUBSCRIBERS_FILE = os.path.join(BASE_DIR, "subscribers.json")
TZ = pytz.timezone("Asia/Ho_Chi_Minh")

# ── JSON Helpers ──
def _load_json(path, default):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def _save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# ── Subscribers ──
def load_subscribers():
    return _load_json(SUBSCRIBERS_FILE, {}).get('subscribers', [])

def save_subscribers(subscribers):
    _save_json(SUBSCRIBERS_FILE, {'subscribers': subscribers})

def add_subscriber(chat_id, username=None, first_name=None):
    subscribers = load_subscribers()
    if not any(s.get('chat_id') == chat_id for s in subscribers):
        subscribers.append({'chat_id': chat_id, 'username': username, 'first_name': first_name})
        save_subscribers(subscribers)
        return True
    return False

def remove_subscriber(chat_id):
    subscribers = load_subscribers()
    new_list = [s for s in subscribers if s.get('chat_id') != chat_id]
    if len(new_list) < len(subscribers):
        save_subscribers(new_list)
        return True
    return False

# ── Bot ──
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL_BASE = os.environ.get("RENDER_EXTERNAL_URL", "https://carmen-intelligent.onrender.com")
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ── Helpers ──
def send_telegram_message(chat_id, text, max_len=4000):
    if len(text) <= max_len:
        bot.send_message(chat_id, text)
        return
    markers = ["🌌 PHÂN TÍCH THIÊN VĂN", "💡 ĐỀ XUẤT CHIẾN LƯỢC"]
    parts = []
    last_idx = 0
    for marker in markers:
        idx = text.find(marker, last_idx)
        if idx > last_idx:
            parts.append(text[last_idx:idx].rstrip())
            last_idx = idx
    parts.append(text[last_idx:])
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) > max_len:
            for i in range(0, len(part), max_len):
                bot.send_message(chat_id, part[i:i + max_len])
        else:
            bot.send_message(chat_id, part)

# ── Flask Routes ──
@app.route('/')
def home():
    return "🪐 Carmen Bot is running"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive Telegram updates via webhook (NO polling, NO 409)."""
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    return "Bad request", 400

@app.route('/broadcast', methods=['POST'])
def broadcast():
    """Generate & broadcast gold report to all Telegram subscribers."""
    try:
        data = get_full_report_data(include_carmen=True)
        report_text = ReportGenerator.generate_report(data)
        subscribers = load_subscribers()
        if not subscribers:
            return jsonify({'status': 'no_subscribers', 'sent': 0}), 200
        sent, failed = 0, []
        for sub in subscribers:
            chat_id = sub.get('chat_id')
            try:
                send_telegram_message(chat_id, report_text)
                sent += 1
            except Exception as e:
                failed.append({'chat_id': chat_id, 'error': str(e)})
                remove_subscriber(chat_id)
        return jsonify({
            'status': 'sent',
            'sent': sent,
            'total': len(subscribers),
            'failed': len(failed),
            'errors': failed[:5]
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/subscribers', methods=['GET'])
def list_subscribers():
    subs = load_subscribers()
    return jsonify({'subscribers': subs, 'count': len(subs)}), 200

# ── Telegram Bot Handlers ──
@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    added = add_subscriber(message.chat.id, message.from_user.username, message.from_user.first_name)
    if added:
        msg = (
            "🪐 Xin chào! Tôi là Carmen.\n\n"
            "Hệ thống phân tích Algorithmic Trading & Vedic Astrology đã sẵn sàng.\n\n"
            "📊 Báo cáo Vàng (XAU/USD) sẽ được gửi tự động:\n"
            "• 🌏 Phiên Á: 07:00 GMT+7 (Thứ 2-6)\n"
            "• 🇺🇸 Phiên Mỹ: 19:00 GMT+7 (Thứ 2-6)\n\n"
            "Bạn đã được thêm vào danh sách nhận báo cáo."
        )
    else:
        msg = (
            "🪐 Bạn đã đăng ký nhận báo cáo rồi.\n\n"
            "📊 Báo cáo Vàng (XAU/USD) sẽ được gửi tự động:\n"
            "• 🌏 Phiên Á: 07:00 GMT+7 (Thứ 2-6)\n"
            "• 🇺🇸 Phiên Mỹ: 19:00 GMT+7 (Thứ 2-6)"
        )
    bot.reply_to(message, msg)

@bot.message_handler(commands=['stop', 'unsubscribe'])
def handle_stop(message):
    removed = remove_subscriber(message.chat.id)
    if removed:
        bot.reply_to(message, "👋 Bạn đã hủy đăng ký nhận báo cáo. Hẹn gặp lại!")
    else:
        bot.reply_to(message, "🤔 Bạn chưa đăng ký nhận báo cáo.")

@bot.message_handler(commands=['status'])
def handle_status(message):
    subs = load_subscribers()
    bot.reply_to(message, f"📊 Hiện có {len(subs)} người nhận báo cáo.")

# ── Entry Point ──
if __name__ == '__main__':
    # Remove any stale webhook & polling state, then register webhook
    try:
        bot.remove_webhook()
    except Exception:
        pass

    webhook_url = f"{WEBHOOK_URL_BASE}/webhook"
    print(f"🔗 Setting webhook: {webhook_url}")
    try:
        bot.set_webhook(url=webhook_url)
        print("✅ Webhook set successfully")
    except Exception as e:
        print(f"⚠️ Failed to set webhook: {e}")

    port = int(os.environ.get('PORT', 8080))
    print(f"🔍 Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)
