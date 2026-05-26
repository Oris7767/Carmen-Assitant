#!/usr/bin/env python3
"""
Birth Chart CSV Cleaner
- Loại bỏ trùng lặp theo id
- Loại bỏ trùng lặp theo nội dung (cùng data — tạo nhiều lần)
- Loại bỏ các birthday sau năm 2026
- Xuất CSV sạch + báo cáo thống kê
"""

import csv
import sys
import re
from datetime import datetime, date
from pathlib import Path
from collections import Counter

INPUT_CSV = Path("/Users/kimssa/.openclaw/media/inbound/birth_chart_inputs_vedicvn---4940ff74-dae3-4b7f-bae0-9fbc7408389e.csv")
OUTPUT_CSV = Path(__file__).parent / "birth_chart_clean.csv"
REPORT_FILE = Path(__file__).parent / "clean_report.md"

YEAR_MAX = 2026
YEAR_MIN = 1900

def parse_birth_date(val):
    """Parse birth_date column, return (date|None, error|None)."""
    val = val.strip()
    if not val:
        return None, "empty"
    try:
        d = datetime.strptime(val, "%Y-%m-%d").date()
        return d, None
    except ValueError:
        return None, f"bad_format:{val}"

def normalize_name(name):
    """Normalize name: lowercase, strip, squish whitespace."""
    return re.sub(r'\s+', ' ', name.strip().lower())

def normalize_location(loc):
    """Normalize location: lowercase, strip, remove extra spaces."""
    if not loc:
        return ""
    return re.sub(r'\s+', ' ', loc.strip().lower())

def make_content_fingerprint(row):
    """
    Create a fingerprint from (name, birth_date, birth_time, location).
    This catches the same person submitting the same data multiple times.
    """
    name = normalize_name(row.get("name", ""))
    bd = row.get("birth_date", "").strip()
    bt = row.get("birth_time", "").strip()
    loc = normalize_location(row.get("location", ""))
    return (name, bd, bt, loc)

def main():
    if not INPUT_CSV.exists():
        print(f"❌ Không tìm thấy file: {INPUT_CSV}")
        sys.exit(1)

    # Read all rows
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        all_rows = list(reader)

    total_raw = len(all_rows)

    # Stats counters
    seen_ids = set()
    dup_ids = 0
    seen_fingerprints = set()
    dup_content = 0
    bad_dates = []
    future_dates = []
    good_rows = []

    for row in all_rows:
        rid = row.get("id", "").strip()

        # 1. Duplicate check by id
        if rid in seen_ids:
            dup_ids += 1
            continue
        seen_ids.add(rid)

        # 2. Parse birth_date
        bd_raw = row.get("birth_date", "")
        bd, err = parse_birth_date(bd_raw)

        if err:
            bad_dates.append((rid, row.get("name", "").strip(), bd_raw))
            continue

        if bd.year > YEAR_MAX:
            future_dates.append((rid, row.get("name", "").strip(), str(bd)))
            continue

        # 3. Reject unrealistically old dates (junk/test entries)
        if bd.year < YEAR_MIN:
            bad_dates.append((rid, row.get("name", "").strip(), f"year<{YEAR_MIN}:{bd}"))
            continue

        # 4. Duplicate check by content (same person, same birth data)
        fp = make_content_fingerprint(row)
        if fp in seen_fingerprints:
            dup_content += 1
            continue
        seen_fingerprints.add(fp)

        good_rows.append(row)

    # Write clean CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(good_rows)

    total_clean = len(good_rows)
    dup_total = dup_ids + dup_content

    # ---- REPORT ----
    report_lines = []
    report_lines.append("# Báo Cáo Làm Sạch CSV Birth Chart\n")
    report_lines.append(f"**File gốc:** {INPUT_CSV.name}")
    report_lines.append(f"**File sạch:** {OUTPUT_CSV.name}")
    report_lines.append(f"**Thời gian:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    report_lines.append("## Tổng Quan")
    report_lines.append(f"| Hạng mục | Số lượng |")
    report_lines.append(f"|----------|---------:|")
    report_lines.append(f"| Tổng số dòng raw | {total_raw} |")
    report_lines.append(f"| Trùng id | {dup_ids} |")
    report_lines.append(f"| Trùng nội dung (cùng birth data) | {dup_content} |")
    report_lines.append(f"| Birthday lỗi (bad format / year<{YEAR_MIN}) | {len(bad_dates)} |")
    report_lines.append(f"| Birthday sau {YEAR_MAX} | {len(future_dates)} |")
    report_lines.append(f"| **Tổng loại bỏ** | **{total_raw - total_clean}** |")
    report_lines.append(f"| **Dòng sạch còn lại** | **{total_clean}** |")
    report_lines.append("")

    if bad_dates:
        report_lines.append("## Birthday Lỗi (loại bỏ)")
        report_lines.append(f"Số lượng: {len(bad_dates)}")
        report_lines.append("| id | name | birth_date_raw |")
        report_lines.append("|----|------|----------------|")
        for rid, name, bd in bad_dates:
            report_lines.append(f"| {rid} | {name} | {bd} |")
        report_lines.append("")

    if future_dates:
        report_lines.append(f"## Birthday Sau Năm {YEAR_MAX} (loại bỏ)")
        report_lines.append(f"Số lượng: {len(future_dates)}")
        report_lines.append("| id | name | birth_date |")
        report_lines.append("|----|------|------------|")
        for rid, name, bd in future_dates:
            report_lines.append(f"| {rid} | {name} | {bd} |")
        report_lines.append("")

    # Year distribution
    year_counter = Counter()
    for row in good_rows:
        bd = datetime.strptime(row["birth_date"].strip(), "%Y-%m-%d").date()
        year_counter[bd.year] += 1

    report_lines.append("## Phân Bố Năm Sinh")
    report_lines.append("| Năm | Số lượng |")
    report_lines.append("|-----|---------:|")
    for y in sorted(year_counter.keys()):
        report_lines.append(f"| {y} | {year_counter[y]} |")
    report_lines.append("")

    report_text = "\n".join(report_lines)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(report_text)
    print(f"\n✅ Done! Clean CSV: {OUTPUT_CSV}")
    print(f"✅ Report: {REPORT_FILE}")

if __name__ == "__main__":
    main()
