# 🪐 Tích Hợp Bot Luận Giải Bản Đồ Sao vào vedicvn.com

> **Cho Cursor AI — CHỈ thêm tính năng mới, KHÔNG sửa code có sẵn.**
> Dự án: `vedicvn/chiem-tinh-ve-dic` (React + Vite + TypeScript + Tailwind)

---

## 📌 Nhiệm Vụ

**Thêm 1 tính năng mới:** Sau khi web tính xong bản đồ sao (VedicChartPage), user có thể bấm "Luận giải chiêm tinh" → gửi dữ liệu chart lên bot API → nhận bài luận giải.

**Chia làm 2 phần:**
- **FREE:** Preview ngắn ~300 từ (miễn phí, xem ngay)
- **FULL:** Luận giải đầy đủ 1500-3000 từ (sau paywall 19k)

**⚠️ QUAN TRỌNG:** 
- KHÔNG sửa/sửa đổi file có sẵn trong project
- CHỈ thêm file mới vào thư mục phù hợp
- Feature này hoàn toàn độc lập — không ảnh hưởng chart engine, form, login, PDF export

---

## 🧠 Kiến Trúc

```
VedicChart.tsx (có sẵn)
    │
    ├── chart data (VedicChartData) ── đã có đầy đủ planets, houses, dashas
    │
    └── [THÊM MỚI] HoroscopeReading.tsx ── Component mới
            │
            ├── Nút "Luận giải chiêm tinh"
            │
            └── horoscopeReadingService.ts ── Service mới
                    │
                    ├── Map VedicChartData → Bot JSON format
                    ├── POST lên bot API
                    └── Trả về { free, full }
```

---

## 📁 File Cần Tạo (4 file mới)

### 1. `src/services/horoscopeReadingService.ts`

**Chức năng:** Chuyển đổi `VedicChartData` (của web) → JSON (bot format) → gọi API → trả kết quả.

```typescript
// ĐÃ CÓ SẴN trong project — dùng types này:
// import { VedicChartData, Planet, House } from '@/components/VedicAstrology/VedicChart';

// Bot API cần JSON format như sau:
interface BotChartRequest {
  metadata: {
    date: string;      // "1998-04-16"
    time: string;      // "02:36"
    timezone: string;  // "Asia/Ho_Chi_Minh"
    latitude: number;
    longitude: number;
  };
  ascendant: {
    longitude: number;
    sign: { name: string; degree: number; minutes: number; };
    nakshatra: { name: string; lord: string; pada: number; startDegree: number; endDegree: number; };
  };
  planets: Array<{
    planet: string;      // "SUN" | "MOON" | "MARS" | ...
    sign: { name: string; longitude: number; minutes: number; };
    house: { number: number; sign: string; };
    isRetrograde: boolean;
    nakshatra: { name: string; lord: string; pada: number; startDegree: number; endDegree: number; };
    aspects: Array<{ planet: string; aspect: string; orb: number; }>;
    aspectingPlanets: string[];
  }>;
  houses: Array<{
    number: number;
    sign: string;
    degree: number;
    planets: string[];
  }>;
  dashas: {
    current: { planet: string; startDate: string; endDate: string; };
    sequence: Array<{ planet: string; startDate: string; endDate: string; duration: number; }>;
  };
}

interface BotReadingResponse {
  free: string;         // ~300 từ, FREE preview
  full: string;         // 1500-3000 từ, FULL reading
  model: string;
  char_count_free: number;
  char_count_full: number;
  rag_chunks_used: number;
}
```

**Công việc service này:**
1. Nhận `VedicChartData` → map từng field sang `BotChartRequest`
   - `Planet.id` → `planet` name (UPPERCASE): "su" → "SUN", "mo" → "MOON"
   - `Planet.sign` (index 0-11) → sign name: ["Aries","Taurus",...,"Pisces"]
   - `Planet.house` → `house.number`
   - `Planet.nakshatra` → giữ nguyên structure
   - `Planet.aspects` → map type: "Conjunction","Trine","Square","Opposition","Sextile"
   - `House.sign` (index) → sign name
   - `Dasha` → dùng `DashaPeriod` types có sẵn

2. Gọi bot API:
```typescript
// Bot endpoint
const BOT_API_URL = "https://votive-horoscope.onrender.com/reading"; // hoặc URL sau khi deploy

async function getReading(chartData: VedicChartData): Promise<BotReadingResponse> {
  const botPayload = mapToBotFormat(chartData);
  
  const response = await fetch(BOT_API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(botPayload),
    signal: AbortSignal.timeout(60000), // 60s timeout
  });
  
  if (!response.ok) throw new Error(`Bot API error: ${response.status}`);
  return response.json();
}
```

3. Cache: dùng `localStorage` với key = MD5 hash của chart data để tránh gọi lại nếu chart giống nhau.

---

### 2. `src/components/VedicAstrology/HoroscopeReading.tsx`

**Chức năng:** Component hiển thị kết quả luận giải — được thêm vào VedicChartPage sau khi chart đã tính xong.

```tsx
// Props: nhận VedicChartData (đã có sẵn từ VedicChart)
// KHÔNG tự gọi chart engine — chỉ dùng dữ liệu đã tính

interface HoroscopeReadingProps {
  chartData: VedicChartData | null;  // null khi chưa có chart
  isLoggedIn: boolean;
}
```

**Cấu trúc component:**
```
┌─────────────────────────────────────────┐
│ 📜 Luận giải chiêm tinh Vệ Đà           │
│                                         │
│  [Trạng thái]                           │
│  ┌─ Chờ chart...                        │  ← chartData === null
│  └────────────────────────────────────  │
│                                         │
│  ┌─ "Nhận luận giải" button ────────┐   │  ← chưa gọi API
│  └──────────────────────────────────┘   │
│                                         │
│  ┌─ Loading... spinner ─────────────┐   │  ← đang gọi API
│  └──────────────────────────────────┘   │
│                                         │
│  ┌─ FREE Preview ──────────────────┐   │
│  │  "Bạn có Lagna ở Bảo Bình...    │   │  ← đã có kết quả
│  │   ...điều thú vị nhất sẽ được   │   │     FREE hiển thị ngay
│  │   hé lộ trong phần luận giải    │   │
│  │   đầy đủ."                      │   │
│  └──────────────────────────────────┘   │
│                                         │
│  ┌─ Paywall ────────────────────────┐   │
│  │  💎 Luận giải đầy đủ             │   │
│  │  Chỉ 19,000đ — 1 lần duy nhất    │   │
│  │  [Mua ngay - QR Momo]            │   │
│  └──────────────────────────────────┘   │
│                                         │
│  ┌─ FULL Reading (sau khi mua) ────┐   │
│  │  1️⃣ 🎭 TÍNH CÁCH & BẢN CHẤT     │   │
│  │  2️⃣ 💼 SỰ NGHIỆP & TÀI CHÍNH    │   │
│  │  ...                             │   │
│  │  6️⃣ 💎 KẾT LUẬN                  │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**States cần handle:**
- `idle` — chart chưa có hoặc chưa bấm nút
- `loading` — đang gọi bot API
- `error` — API lỗi (hiển thị lỗi + retry)
- `free` — đã có FREE, chưa unlock FULL
- `full` — đã unlock FULL (sau paywall)

**Style:** Dùng Tailwind, theme tối (gradient `from-votive-text` như VedicChartPage). Dùng card component có sẵn: `@/components/ui/card`.

---

### 3. `src/pages/VedicChartPage.tsx` — **CHỈ SỬA NHỎ**

**Chỉ thêm 1 dòng:** Import `HoroscopeReading` và thêm vào JSX sau phần chart.

**File này đã tồn tại — chỉ thêm:**

```tsx
// Thêm import ở đầu file
import HoroscopeReading from '../components/VedicAstrology/HoroscopeReading';

// Trong JSX, sau phần <VedicChart />, thêm:
<div className="mt-8">
  <HoroscopeReading 
    chartData={chartData} 
    isLoggedIn={user !== null}
  />
</div>
```

⚠️ **Lưu ý:** `chartData` cần được lấy từ state của VedicChart. Nếu VedicChart dùng internal state, cần:
- **Cách A (khuyên dùng):** Cho HoroscopeReading tự import VedicChartData và tự quản lý state — không cần sửa VedicChart
- **Cách B:** Nếu VedicChart đã expose chartData qua props/callback — dùng luôn

---

### 4. `.env` — **Thêm biến mới**

Thêm vào `.env` (nếu chưa có thì tạo mới ở root project):
```
VITE_HOROSCOPE_BOT_URL=https://votive-horoscope.onrender.com
```

Dùng: `import.meta.env.VITE_HOROSCOPE_BOT_URL`

---

## 🔌 Bot API Endpoint

Sau khi deploy horoscope bot lên Render, URL là:

```
POST https://votive-horoscope.onrender.com/reading
```

### Request Body (JSON)
Xem format đầy đủ ở `horoscope-bot/data/sample_api_response.json` (trong workspace).

### Response
```json
{
  "free": "Bạn có Lagna ở Bảo Bình (Aquarius) với Sao Mộc và Sao Kim cùng tọa lạc tại Nhà 1...",
  "full": "🔮 LUẬN GIẢI LÁ SỐ CHIÊM TINH VỆ ĐÀ\n\n1️⃣ 🎭 TÍNH CÁCH & BẢN CHẤT\n...",
  "model": "gemini",
  "char_count_free": 1845,
  "char_count_full": 15230,
  "rag_chunks_used": 12
}
```

---

## 🧪 Test Flow

1. Vào `/vedic-chart` → nhập DOB/TOB/POB → bấm "Xem bản đồ sao"
2. Chart hiển thị (South Indian Chart + bảng planets/houses/dashas) — **đã có sẵn**
3. **TÍNH NĂNG MỚI:** Cuộn xuống thấy "📜 Luận giải chiêm tinh Vệ Đà"
4. Bấm "Nhận luận giải" → loading 15-25s
5. FREE preview hiện ra
6. Paywall 19k → "Mua ngay" → unlock FULL reading

---

## ❌ KHÔNG ĐƯỢC LÀM

| Việc | Lý do |
|------|-------|
| Sửa file VedicChart.tsx | Đã hoàn chỉnh, không cần chạm |
| Sửa vedicAstroService.ts | Service chart engine riêng, không liên quan |
| Sửa BirthChartForm | Form nhập liệu riêng |
| Sửa App.tsx routing | Không cần route mới; feature gắn vào VedicChartPage |
| Sửa ChatBot | Component riêng cho hỗ trợ |
| Sửa PDF export | Tính năng riêng |
| Sửa Login/Auth | Auth module riêng |
| Sửa Supabase | Database riêng |

**Nguyên tắc:** Feature mới = file mới. Không regression.

---

## 📚 Tham Khảo

- **Sample chart JSON:** `~/.openclaw/workspace/horoscope-bot/data/sample_api_response.json`
- **Bot API code:** `~/.openclaw/workspace/horoscope-bot/api/main.py`
- **Bot API schema:** `~/.openclaw/workspace/horoscope-bot/api/schemas.py` (Pydantic models = type reference)
- **Types có sẵn trong web:** `VedicChartData`, `Planet`, `House`, `NakshatraInfo`, `DashaPeriod`, `Aspect` — tất cả export từ `@/components/VedicAstrology/VedicChart`
