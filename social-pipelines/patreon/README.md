# 🔴 Aether — Patreon Social Pipeline

> Brand: **Aether Astro-Quant Engine** — Gold Trading Quant Data
> **🔴 ĐỘC LẬP TUYỆT ĐỐI**

## ⚠️ RULES — KHÔNG BAO GIỜ VI PHẠM

| ✅ Được | ❌ Không được |
|---------|--------------|
| Post Aether content lên Patreon + X | Post Aether content lên Votive Academy |
| Dùng scripts trong folder này | Post Aether content lên YouTube La Bàn Số Mệnh |
| Chỉ dùng cho Aether brand | Post Aether content lên Quant EA Labs web |

## Post lên X (Twitter)

```bash
cd social-pipelines/patreon/scripts

# API (cần X API token hợp lệ)
node social_poster.js \
  --content ./post.md \
  --image ./image.jpg \
  --platform x

# Browser automation
node x_poster.js \
  --content ./post.md \
  --image ./image.jpg
```

## Post lên Patreon

```bash
cd social-pipelines/patreon/scripts
node patreon_poster.js
node patreon_publish.js
```

## Credentials

Lưu trong `scripts/.env` — X API keys cho Aether brand.

## Database

Data gốc vẫn ở `patreon-db/` (529MB — CSV data, không copy vào đây).
