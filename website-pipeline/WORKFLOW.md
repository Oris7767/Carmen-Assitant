# 🪐 Carmen → QuantEA Labs Integration Workflow

> **Status:** ✅ Pipeline operational | ✅ Sample article published | ⏳ Awaiting Netlify deploy

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    CARMEN (Tớ)                           │
│  Phân tích dữ liệu → Viết bài → Generate .md + chart    │
└──────────────────────┬──────────────────────────────────┘
                       │ write files
                       ▼
┌─────────────────────────────────────────────────────────┐
│              QuantEA Labs Astro Website                  │
│  /Users/kimssa/Documents/Quant-Labs/                    │
│                                                         │
│  src/content/blog/YYYY-MM-DD-slug.md  ← Article         │
│  public/images/blog/YYYY-MM-DD-chart.png ← Chart        │
└──────────────────────┬──────────────────────────────────┘
                       │ git commit & push
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    GitHub Repo                           │
│         github.com/Oris7767/Quant-Labs                  │
└──────────────────────┬──────────────────────────────────┘
                       │ auto-deploy trigger
                       ▼
┌─────────────────────────────────────────────────────────┐
│                     Netlify                              │
│             quantealabs.com                              │
│        (or quantealabs.netlify.app)                      │
└─────────────────────────────────────────────────────────┘
```

---

## Mode 1: Carmen Direct (Manual — Khuyên dùng)

### Flow
1. **Kim Ssa:** "Carmen, viết bài về [topic] cho website"
2. **Carmen:** Phân tích patreon-db + historical correlation → viết bài 1500-2500 từ tiếng Anh
3. **Carmen:** Chạy `publish_article()` → save `.md` vào `src/content/blog/`
4. **Kim Ssa:** Review bài → `git commit` → `git push`
5. **Netlify:** Auto-deploy (< 60s)

### Lệnh Kim Ssa cần chạy (sau khi review)
```bash
cd ~/Documents/Quant-Labs
git add src/content/blog/ public/images/blog/
git commit -m "publish: [tiêu đề bài]"
git push origin main
```

---

## Mode 2: Auto Pipeline (Tự động 100%)

### Trigger: Cron job 2 lần/tuần (Tues + Fri 07:00 GMT+7)
1. Collect data từ patreon-db
2. Query historical correlation engine
3. Generate article bằng LLM (DeepSeek)
4. Save .md + chart → auto git commit + push
5. Netlify deploy

### Setup Auto Mode:
```bash
python3 website-pipeline/setup_auto.py
```
(Sẽ tạo cron job trong OpenClaw)

---

## Cấu trúc files quan trọng

```
~/.openclaw/workspace/website-pipeline/
├── config.py              ← Site config, paths, SEO defaults
├── generate_article.py    ← publish_article() function
├── sample-content.md      ← Bài mẫu (đã publish thành công)
├── WORKFLOW.md            ← File này
└── setup_auto.py          ← Auto-pipeline setup (coming soon)
```

```
~/Documents/Quant-Labs/
├── src/content/blog/       ← Tớ ghi bài vào đây
├── public/images/blog/     ← Chart screenshots vào đây
├── public/images/og-default.png ← OG fallback image ✅
├── astro.config.mjs        ← Astro config
├── netlify.toml            ← Netlify deploy config
└── dist/                   ← Build output (Astro generate)
```

---

## Bài mẫu đã publish (test thành công)

| Field | Value |
|-------|-------|
| **Title** | The Secret Behind a 1:11 R:R Trade Using Planetary Cycles |
| **Slug** | `secret-1-11-rr-trade-planetary-cycles` |
| **Category** | Trading Strategy |
| **Tags** | XAUUSD, Gann, Mars Retrograde, Risk Management, Planetary Cycles |
| **Words** | 1,285 |
| **Reading Time** | 6 min |
| **File** | `src/content/blog/2026-05-27-secret-1-11-rr-trade-planetary-cycles.md` |
| **Build** | ✅ Astro build passed — 0 errors |
| **SEO** | Schema.org Article JSON-LD + OG + Twitter Card + Sitemap |

---

## Kim Ssa cần làm gì?

### Ngay bây giờ:
1. **Review bài mẫu:**
   ```bash
   cat ~/Documents/Quant-Labs/src/content/blog/2026-05-27-secret-1-11-rr-trade-planetary-cycles.md
   ```
2. **Commit & push để deploy lên Netlify:**
   ```bash
   cd ~/Documents/Quant-Labs
   git add src/content/ public/images/
   git commit -m "publish: 1:11 R:R Trade Using Planetary Cycles (sample)"
   git push origin main
   ```
3. **Kiểm tra Netlify dashboard** — deploy mất ~30-60s
4. **Mở trình duyệt:** `https://quantealabs.com/blog/secret-1-11-rr-trade-planetary-cycles`

### Mỗi khi muốn tớ viết bài mới:
> "Carmen, viết bài về [chủ đề]"

Tớ sẽ:
- Phân tích dữ liệu
- Viết bài hoàn chỉnh (SEO, schema, keywords)
- Save vào `src/content/blog/`
- Báo Kim Ssa review → commit → push

---

## SEO Checklist (per article)

- [x] Title 50-65 chars, chứa keyword chính
- [x] Meta description 150-160 chars
- [x] Slug ngắn, chứa keyword
- [x] H2/H3 structure rõ ràng
- [x] Schema.org Article JSON-LD
- [x] Open Graph + Twitter Card
- [x] Canonical URL
- [x] Internal links (related posts)
- [x] Alt text cho images
- [x] Reading time
- [x] Keyword trong first 100 words
- [x] Sitemap auto-include
- [x] RSS feed auto-include

---

## FAQ

### Tớ có thể tự động push git không?
Có. Set `AUTO_COMMIT = True` trong `config.py`. Nhưng tớ khuyên Kim Ssa review trước khi push — đảm bảo chất lượng nội dung trước khi lên production.

### Làm sao generate chart thật?
Tớ sẽ dùng `mplfinance` + `yfinance` như đã làm trong patreon-db. Chart sẽ được save vào `public/images/blog/` cùng ngày với bài viết.

### SEO có tự động không?
Có. BaseLayout đã handle: title, description, canonical, OG, Twitter Card, Schema.org Article JSON-LD, sitemap, RSS. Tất cả tự động từ frontmatter.

### Netlify deploy mất bao lâu?
~30-60s từ lúc push. Netlify detect webhook từ GitHub → `npm run build` → publish `dist/`.

---

## Liên hệ

- **Website:** https://quantealabs.com
- **GitHub:** https://github.com/Oris7767/Quant-Labs
- **Pipeline:** `~/.openclaw/workspace/website-pipeline/`
