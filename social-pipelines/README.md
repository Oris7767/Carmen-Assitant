# 🪐 Social Pipelines — Brand Map

> **Mỗi brand post content độc lập. Thư viện & data dùng chung.**

---

## 🏗️ Kiến Trúc Tổng Thể

```
SHARED LAYER ─────────────────────────────────────┐
├── RAG Gold (Aether database, 18 năm)            │
├── RAG Chiêm tinh Vệ Đà (corpus, FAISS)          │
├── Swiss Ephemeris (pyswisseph)                  │
├── Aether database (patreon-db/, 529MB)          │
└── Patreon post templates                        │
                                                  │
                      ▼                            ▼
BRAND LAYER ───────────────────────────────────────────────────
├── Votive Academy     → FB, IG, X     (social-pipelines/votive/)
├── Aether / Patreon   → Patreon, X    (social-pipelines/patreon/)
├── La Bàn Số Mệnh     → YouTube       (youtube-pipeline/)
├── Quant EA Labs      → Web           (website-pipeline/)
└── VedicVN Blog       → Web           (blog-pipeline/)
```

**Thư viện dùng chung cho nhiều brand:**
| Thư viện | Dùng bởi |
|----------|----------|
| **RAG Gold** | Bot trade, Aether post, Quant EA Labs post |
| **RAG Chiêm tinh** | Horoscope bot, Votive Assistant, Cron posts |
| **Swiss Ephemeris** | Toàn bộ Votive (bot horoscope, bot trade, Votive VA, Vedic Weekly, YouTube) |
| **Aether Database** | Aether posts (Patreon + X), Quant EA Labs |

---

## 1. 🪐 Votive Academy — Chiêm tinh Vệ Đà
| Mục | Chi tiết |
|-----|----------|
| **Website** | https://votive.vedicvn.com |
| **Nội dung** | Chiêm tinh Vệ Đà, khóa học, dịch vụ |
| **Nền tảng** | Facebook, Instagram, X |
| **Pipeline** | `votive/` |
| **Ngôn ngữ** | Tiếng Việt |
| **Từ khoá cấm** | Không "bot", "AI", "La Bàn Số Mệnh" |
| **Script FB/IG** | `votive/scripts/meta_post.py` |
| **Script X** | `votive/scripts/x_poster.js` |

## 2. 🔴 Aether — Patreon / Quant Data (ĐỘC LẬP)
| Mục | Chi tiết |
|-----|----------|
| **Brand** | Aether Astro-Quant Engine |
| **Nội dung** | Gold trading analysis, Gann, Fibonacci |
| **Nền tảng** | Patreon, X |
| **Pipeline** | `patreon/` |
| **Ngôn ngữ** | Tiếng Việt |
| **🔴 CẤM TUYỆT ĐỐI** | Không post content Aether sang Votive, YouTube, hay bất kỳ brand nào khác |
| **Data** | `patreon-db/` (database riêng, 529MB) |
| **Script X** | `patreon/scripts/x_poster.js` |
| **Script social** | `patreon/scripts/social_poster.js` |
| **Script Patreon** | `patreon/scripts/patreon_poster.js` |
| **Credentials** | `patreon/scripts/.env` |

## 3. 📺 La Bàn Số Mệnh — YouTube
| Mục | Chi tiết |
|-----|----------|
| **Nội dung** | Video chiêm tinh, shorts |
| **Pipeline** | `youtube-pipeline/` (giữ nguyên) |
| **Thư viện chung** | RAG Chiêm tinh, Swiss Ephemeris |

## 4. 🌐 VedicVN / Quant EA Labs — Web
| Mục | Chi tiết |
|-----|----------|
| **Nội dung** | Blog, website content |
| **Pipeline** | `website-pipeline/`, `blog-pipeline/` (giữ nguyên) |
| **Thư viện chung** | RAG Gold, Aether Database |

---

## 🔥 Rules

```
Votive Content  → FB, IG, X (không chạm Patreon)
Aether Content  → Patreon, X (không chạm Votive, YouTube, Quant EA Labs)
La Bàn Số Mệnh  → YouTube (riêng)
Quant EA Labs   → Web (riêng)

# Thư viện dùng CHUNG (dùng được mọi nơi)
RAG Gold ├── Bot trade ├── Aether post ├── Quant EA Labs
RAG Chiêm ├── Horoscope ├── Votive VA ├── Cron Vedic ├── YouTube
Sweph    ├── Mọi bot Votive ├── Vedic Weekly ├── YouTube
```
