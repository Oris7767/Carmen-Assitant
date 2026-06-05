# 🖥️ VPS Reference — 160.22.106.46

> **Host:** vps-mindfulliving98-690  
> **OS:** Ubuntu 24.04 LTS  
> **Specs:** 4 vCPU (Intel Xeon Gold 6133) | 4GB RAM + 2GB Swap | 40GB Disk  
> **Timezone:** Asia/Ho_Chi_Minh (GMT+7)  
> **SSH:** root / lV9!bVFKhqW@

---

## 🌐 Service Endpoints

| Service | Port | URL |
|---|---|---|
| **OpenClaw Gateway** | 18789 | http://160.22.106.46:18789/ |
| **Votive Horoscope Bot** | 8000 | http://160.22.106.46:8000/ |
| **Vedic Astrology API** | 10000 | http://160.22.106.46:10000/api/health |
| **Carmen Telegram Bot** | 5000 | http://160.22.106.46:5000/health |

---

## 🔮 Votive Horoscope Bot (Port 8000) — HTTPS

**URL chính thức:** https://horoscope.vedicvn.sbs/

```
POST https://horoscope.vedicvn.sbs/reading/free   — FREE preview (~60s)
POST https://horoscope.vedicvn.sbs/reading/full   — FULL reading + RAG (3-5min)
GET  https://horoscope.vedicvn.sbs/health          — Health check
GET  https://horoscope.vedicvn.sbs/debug/config    — Debug config
```

**Model:** MiMo 2.5 Pro (Xiaomi Token Plan)  
**RAG:** 634 chunks (Bhrigu Samhita, BPHS, Nakshatras, Karakatvas...)  
**API Key:** `MIMO_API_KEY` in `/root/horoscope-bot/.env`  
**SSL:** Let's Encrypt (auto-renew via certbot)

---

## 🪐 OpenClaw Gateway (Port 18789)

**Dashboard UI:** http://160.22.106.46:18789/

### 🔐 Auth Token
> **Lấy từ config trên VPS:**  
> SSH vào VPS rồi chạy:
> ```bash
> cat /root/.openclaw/openclaw.json | python3 -c "import sys,json; c=json.load(sys.stdin); print(c['gateway']['auth']['token'])"
> ```

### 🌐 Cách kết nối từ Local (Mac) vào VPS Gateway

**Cách 1 — Web Browser (dễ nhất):**
1. Mở http://160.22.106.46:18789/ trên trình duyệt
2. Nhập auth token (lấy từ lệnh trên)
3. Dùng được ngay — chat, tools, mọi thứ

**Cách 2 — Kết nối OpenClaw CLI từ Mac vào VPS:**
```bash
# Set gateway token
export OPENCLAW_GATEWAY_TOKEN="<paste-token-here>"

# Kết nối tới VPS gateway
openclaw gateway call --gateway-url http://160.22.106.46:18789 health
```

**Cách 3 — SSH Tunnel (nếu muốn bảo mật hơn):**
```bash
# Từ Mac, chạy:
ssh -L 18789:127.0.0.1:18789 root@160.22.106.46

# Sau đó mở http://127.0.0.1:18789/ trên browser local
```

---

## 🔧 System Services (systemd)

```bash
# Xem trạng thái tất cả services
systemctl list-units --type=service --state=running | grep -E 'openclaw|carmen|votive'

# Từng service:
systemctl status openclaw.service              # OpenClaw Gateway
systemctl status votive-astrologybot.service   # Horoscope Bot
systemctl status carmen-bot.service            # Flask Bot
systemctl status carmen-bot-poller.service     # Telegram Poller
systemctl status vedic-astrology-api.service   # Vedic API

# Restart:
systemctl restart <service-name>

# Xem logs:
journalctl -u <service-name> --no-pager -n 50
journalctl -u votive-astrologybot.service -f   # follow mode
```

---

## 🗂️ Directory Structure

```
/root/
├── .openclaw/
│   ├── openclaw.json          # OpenClaw config (chứa auth token)
│   └── workspace/             # Workspace (AGENTS.md, MEMORY.md, v.v.)
├── horoscope-bot/             # Votive Astrology Bot (port 8000)
│   ├── api/main.py            # FastAPI server
│   ├── engine/                # RAG, prompts, chart adapter
│   └── corpus/                # Vedic texts + embeddings
├── jyotisha-celestial-nexus/  # Vedic Astrology API (port 10000)
│   └── dist/                  # Built server
```

---

## 🔥 Firewall (UFW)

| Port | Service |
|---|---|
| 22/tcp | SSH |
| 18789/tcp | OpenClaw Gateway |
| 8000/tcp | Votive Horoscope Bot |
| 10000/tcp | Vedic Astrology API |
| 5000/tcp | Carmen Telegram Bot |

---

## 🤖 Telegram Bot

Bot đang chạy polling mode (không cần webhook HTTPS).  
- Token: lưu trong `/root/.openclaw/workspace/.env` và `/root/horoscope-bot/.env`  
- Subscribers: `/root/.openclaw/workspace/subscribers.json`  
- Cron broadcast: 07:00 & 19:00 GMT+7 (Mon-Fri)

---

## 📅 Cron Jobs

```bash
# Broadcast gold reports
0 7 * * 1-5 curl -sf -X POST http://127.0.0.1:5000/broadcast
0 19 * * 1-5 curl -sf -X POST http://127.0.0.1:5000/broadcast
```
