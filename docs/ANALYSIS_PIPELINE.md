# 🔄 Phân Tích Vàng (XAUUSD) — Luồng Phân Tích

## 📌 Tổng Quan

| | **Luồng Cũ (Script-Only)** | **Luồng Mới (Carmen AI)** |
|---|---|---|
| **Phiên bản** | v1 — Rule-based | v2 — AI-Hybrid |
| **Engine** | Python thuần | Python + Gemini Pro (Flash) |
| **Call Lệnh** | Hardcoded rules | AI reasoning + structured JSON |
| **Confidence** | Không có | 0.0 → 1.0 |
| **Macro Context** | Static text | AI phân tích real-time |
| **Risk Assessment** | SL/TP hardcoded | AI đánh giá key risks |

---

## 📊 Luồng Phân Tích Cũ (v1 — Script-Only)

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: DATA FETCH                                         │
│  • Giá vàng M30 (yfinance GC=F, 48 candles)                │
│  • Tin tức Yahoo Finance (3 bài)                            │
│  • Macro Calendar (ForexFactory XML)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: TECHNICAL ENGINES                                  │
│  • TA Engine: Swing High/Low, Trend, Fibonacci              │
│  • Gann Engine: Square of 9, Fan angles                     │
│  • Gann Date Engine: 630-day cycle                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: ASTROLOGY ENGINES                                  │
│  • Hora Engine: Planetary hours (Chaldean order)            │
│  • Astro Engine: Moon sign, nakshatra, aspects, combust     │
│  • Vedic API: External service (vedicvn-api.onrender.com)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: RULE-BASED CALL LỆNH                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ if trend == "UP" and fib_support exists:            │    │
│  │   → BUY LIMIT                                       │    │
│  │   SL = swing_low - 15                               │    │
│  │   TP1 = next Fibo, TP2 = Gann 90°                   │    │
│  │                                                     │    │
│  │ if trend == "DOWN" and fib_resist exists:           │    │
│  │   → SELL LIMIT                                      │    │
│  │   SL = swing_high + 15                              │    │
│  │   TP1 = next Fibo, TP2 = Gann 90°                   │    │
│  │                                                     │    │
│  │ if noisy_hora (Moon/Venus):                         │    │
│  │   → Add warning, wait for confirmation              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ❌ KHÔNG CÓ:                                               │
│  • Confidence score                                         │
│  • AI reasoning                                             │
│  • Macro context analysis                                   │
│  • Risk assessment beyond SL/TP                             │
│  • Synthesis of technical + astro + macro                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: REPORT GENERATOR                                   │
│  • Format text, assemble sections                           │
│  • Static macro assessment                                  │
│  • Send to Telegram                                         │
└─────────────────────────────────────────────────────────────┘
```

### 🔑 Điểm Yếu Luồng Cũ

1. **Call lệnh cứng nhắc** — `if trend==UP → BUY`, không có nuance
2. **Không có confidence** — không biết khi nào nên trade, khi nào nên hold
3. **Macro assessment static** — hardcode "Tin tức tập trung vào sự chờ đợi..."
4. **Không có synthesis** — technical và astrology chạy riêng biệt, không kết hợp
5. **Risk management basic** — SL/TP hardcoded, không adapt theo market conditions

---

## 🧠 Luồng Phân Tích Mới (v2 — Carmen AI)

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: DATA FETCH                                         │
│  • Giá vàng M30 (yfinance GC=F, 48 candles)                │
│  • Tin tức Yahoo Finance (3 bài)                            │
│  • Macro Calendar (ForexFactory XML)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: TECHNICAL ENGINES                                  │
│  • TA Engine: Swing High/Low, Trend, Fibonacci              │
│  • Gann Engine: Square of 9, Fan angles                     │
│  • Gann Date Engine: 630-day cycle                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: ASTROLOGY ENGINES                                  │
│  • Hora Engine: Planetary hours (Chaldean order)            │
│  • Astro Engine: Moon sign, nakshatra, aspects, combust     │
│  • Vedic API: External service (vedicvn-api.onrender.com)   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  🆕 STEP 4: CARMEN AI ANALYSIS (Gemini Pro Flash)           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Input: Toàn bộ data từ Step 1-3                     │    │
│  │                                                     │    │
│  │ Carmen phân tích:                                   │    │
│  │                                                     │    │
│  │ 1. TECHNICAL ASSESSMENT:                            │    │
│  │    • Price vs Fibonacci — vị trí chính xác          │    │
│  │    • Gann key levels — mốc quan trọng nhất           │    │
│  │    • Trend strength — strong/moderate/weak          │    │
│  │    • Confluence zones — vùng hội tụ tín hiệu         │    │
│  │                                                     │    │
│  │ 2. ASTRO ASSESSMENT:                                │    │
│  │    • Moon sentiment — impact lên market             │    │
│  │    • Hora signal — current + next hora              │    │
│  │    • Key aspects — tight orb ≤8°                    │    │
│  │    • Combust warnings — hành tinh bị yếu             │    │
│  │    • Retrograde notes — energy hướng nội            │    │
│  │                                                     │    │
│  │ 3. MACRO CONTEXT:                                   │    │
│  │    • News sentiment analysis                        │    │
│  │    • High-impact calendar events                    │    │
│  │    • USD/yield pressure assessment                  │    │
│  │                                                     │    │
│  │ 4. SYNTHESIS:                                       │    │
│  │    • Where technical + astro + macro agree?         │    │
│  │    • Where do they conflict?                        │    │
│  │    • Confidence score (0.0 → 1.0)                   │    │
│  │                                                     │    │
│  │ Output: Structured JSON                             │    │
│  │ {                                                   │    │
│  │   "bias": "BULLISH|BEARISH|NEUTRAL|MIXED",         │    │
│  │   "confidence": 0.65,                               │    │
│  │   "entry": {                                        │    │
│  │     "direction": "BUY|SELL|HOLD",                   │    │
│  │     "price": 4525.0,                                │    │
│  │     "reasoning": "Chi tiết lý do"                   │    │
│  │   },                                                │    │
│  │   "stop_loss": 4498.0,                              │    │
│  │   "take_profit": [4539.52, 4561.2],                 │    │
│  │   "risk_reward": 1.34,                              │    │
│  │   "key_risks": ["risk 1", "risk 2"],                │    │
│  │   "reasoning_summary": "Tổng hợp 3-5 câu"           │    │
│  │ }                                                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: REPORT GENERATOR                                   │
│  • Ưu tiên: Carmen AI analysis (nếu có)                    │
│  • Fallback: Rule-based logic (nếu AI lỗi/không có key)    │
│  • Format report với confidence badge                      │
│  • 🟢 Confidence cao (≥0.8)                                │
│  • 🟡 Confidence trung bình (≥0.6)                         │
│  • 🟠 Confidence thấp (≥0.4)                               │
│  • 🔴 Confidence rất thấp (<0.4)                           │
│  • Send to Telegram                                        │
└─────────────────────────────────────────────────────────────┘
```

### 🆕 Điểm Mới Luồng Mới

| Tính Năng | Luồng Cũ | Luồng Mới |
|---|---|---|
| **Call Lệnh** | `if trend==UP → BUY` | AI reasoning + structured JSON |
| **Confidence** | ❌ Không có | ✅ 0.0 → 1.0 |
| **Macro Context** | Hardcoded text | AI phân tích real-time |
| **Risk Assessment** | SL/TP hardcoded | AI đánh giá key risks |
| **Synthesis** | ❌ Không | ✅ Technical + Astro + Macro |
| **Bias** | ❌ Không | ✅ BULLISH/BEARISH/NEUTRAL/MIXED |
| **Trend Strength** | ❌ Không | ✅ strong/moderate/weak |
| **Confluence Zones** | ❌ Không | ✅ AI xác định vùng hội tụ |

### 🔑 Điểm Mạnh Luồng Mới

1. **AI reasoning** — Carmen giải thích tại sao BUY/SELL, không phải hardcoded
2. **Confidence score** — biết khi nào nên trade (cao) hay hold (thấp)
3. **Synthesis** — kết hợp technical + astrology + macro thành 1 conclusion
4. **Adaptive SL/TP** — AI tính toán dựa trên market conditions, không hardcoded
5. **Risk awareness** — key_risks từ AI, không chỉ SL/TP
6. **Graceful fallback** — nếu AI lỗi, vẫn dùng rule-based logic

---

## 📁 File Structure

### Luồng Cũ
```
run_bot.py
  ├── data_fetcher.py
  ├── ta_engine.py
  ├── gann_engine.py
  ├── hora_engine.py
  ├── astro_engine.py
  └── report_generator.py (rule-based call lệnh)
```

### Luồng Mới
```
run_bot.py
  ├── data_fetcher.py
  ├── ta_engine.py
  ├── gann_engine.py
  ├── hora_engine.py
  ├── astro_engine.py
  ├── 🆕 carmen_analyst.py (Gemini Pro Flash)
  └── report_generator.py (AI-first, rule-based fallback)
```

---

## 🔧 Configuration

### Environment Variables
```bash
# .env file
GEMINI_API_KEY=AIzaSy...xxx

# Lấy từ: https://aistudio.google.com/app/apikey
```

### Model
- **Default:** `gemini-2.5-flash`
- **Temperature:** 0.3 (consistent analysis)
- **Max tokens:** 8192

### Cache
- File: `.carmen_cache.json`
- TTL: 5 minutes
- Condition: Price within $5

---

## 📊 Example Output Comparison

### Luồng Cũ (Rule-Based)
```
📌 CALL LỆNH: ⬆️ BUY LIMIT
• Entry: $4517.2 (vùng hỗ trợ Fibo 0.2126)
• SL: $4473.3
• TP1: $4524.75 (50% pos) | TP2: $4735.1
• R:R = 1:4.4 (dựa trên TP2)
✅ Xu hướng UP + Hora ổn định — Buy on dips.
```

### Luồng Mới (Carmen AI)
```
🧠 CARMEN AI PHÂN TÍCH — MIXED | Confidence: 60% 🟡 Confidence trung bình

📌 LỆNH: ⬆️ BUY LIMIT
• Entry: $4525.0
  → Giá đang kiểm tra kháng cự Fibonacci 0.5, Jupiter Hora hỗ trợ đà tăng
• SL: $4498.0
• TP1: $4539.52 (50% pos) | TP2: $4561.2
• R:R = 1:1.34 (dựa trên TP2)

📝 CARMEN'S REASONING:
Xu hướng M30 đang tăng và Jupiter Hora hiện tại hỗ trợ đà tăng, với giá đang kiểm tra kháng cự Fibonacci 0.5 ($4524.75). Tuy nhiên, các yếu tố chiêm tinh mạnh mẽ, đặc biệt là Moon trong Cự Giải, giai đoạn First Quarter và các góc chiếu Square của Mars-Pluto, Ketu-Sun/Uranus, cảnh báo về một thị trường biến động cao, dễ có sudden reversals.

🔴 KEY RISKS:
⚠️ Moon trong Cự Giải + First Quarter = cảm xúc cao, dễ panic
⚠️ Mars Square Pluto = sharp moves, stop hunts
⚠️ Ketu Square Sun = disruption, khó predict direction
```

---

## 🚀 Deployment

### Local (Mac)
```bash
cd /Users/kimssa/.openclaw/workspace
nohup python3 telegram_bot.py > telegram_bot.log 2>&1 &
```

### Render
```yaml
# render.yaml
build:
  command: pip install -r requirements.txt
run:
  command: python3 telegram_bot.py
```

### Environment Variables (Render)
```
GEMINI_API_KEY=AIzaSy...xxx
BOT_TOKEN=854240...xxx
```

---

## 📝 Notes

- **Gemini 2.5 Pro** bắt buộc thinking mode → không phù hợp cho structured JSON
- **Gemini 2.5 Flash** → fast, cheap, perfect cho analysis task
- **Fallback mode** → nếu AI lỗi hoặc không có key, vẫn dùng rule-based logic
- **Cache** → tránh duplicate API calls (5 min TTL, price within $5)

---

*Created: 2026-05-22 | Version: v2 (Carmen AI)*
