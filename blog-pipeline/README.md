# Blog Publishing Pipeline — Vedic VN

## Trạng thái

**3 bài đầu đã publish:** 2026-05-31 ✅

| Tuyến | Bài | Slug | Status |
|-------|-----|------|--------|
| Tuyến 2 (Thời không) | Sao Mộc quá cảnh 2026 | `jupiter-transit-2026-0` | ✅ Live |
| Tuyến 1 (Pain points) | Sao Thổ trong bản đồ sao | `saturn-career-breakthrough-0` | ✅ Live |
| Tuyến 3 (Kiến thức) | Cung Mọc (Lagna) | `lagna-ascendant-guide-0` | ✅ Live |

## Schedule

- **Cron (VPS):** Thứ 3 & Thứ 6, 07:00 GMT+7 (UTC 0 `0 0 * * 2,5`)
- **VPS IP:** `160.22.106.46` — chạy ổn định kể cả local tắt
- **Deploy path:** `/root/blog-pipeline/`
- Mỗi lần chạy publish 1 bài mới (luân phiên 3 tuyến)
- Mỗi bài có: case study từ birth chart bank (~10k records), internal link → `/vedic-chart`, social links
- **Log file:** `/root/blog-pipeline/publish.log`

## Lệnh

```bash
# Publish bài tiếp theo
python3 publish.py --run

# Kiểm tra trạng thái
python3 publish.py --status

# Publish specific series
python3 publish.py --series 1 --run
```

**Script:** `/Users/kimssa/.openclaw/workspace/blog-pipeline/publish.py`
**Dữ liệu:** 10,143 birth chart records (`birth-chart-bank-data/`)
**Tags sử dụng:** vedic, chiemtinh, dudoan, kienthuc, taichinh, healing, numerology
