#!/usr/bin/env python3
"""
Age group analysis on the clean birth chart CSV.
"""

import csv
from pathlib import Path
from datetime import date, datetime
from collections import Counter

INPUT = Path(__file__).parent / "birth_chart_clean.csv"
REPORT = Path(__file__).parent / "age_group_report.md"

# Reference date: mid-2026
REF_DATE = date(2026, 5, 24)

AGE_GROUPS = [
    ("0-5", 0, 5),
    ("6-11", 6, 11),
    ("12-17", 12, 17),
    ("18-24", 18, 24),
    ("25-34", 25, 34),
    ("35-44", 35, 44),
    ("45-54", 45, 54),
    ("55-64", 55, 64),
    ("65+", 65, 999),
]

def compute_age(birth_date_str):
    try:
        bd = datetime.strptime(birth_date_str.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None
    # Age at reference date
    age = REF_DATE.year - bd.year
    if (REF_DATE.month, REF_DATE.day) < (bd.month, bd.day):
        age -= 1
    return age

rows = []
with open(INPUT, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

total = len(rows)

# Age per row
age_counter = Counter()
group_counter = Counter()
age_details = []  # (age, group_label) for percentiles

for row in rows:
    age = compute_age(row.get("birth_date", ""))
    if age is None:
        continue
    age_counter[age] += 1
    age_details.append(age)

    for label, lo, hi in AGE_GROUPS:
        if lo <= age <= hi:
            group_counter[label] += 1
            break
    else:
        group_counter["unknown"] += 1

total_with_age = sum(age_counter.values())
sorted_ages = sorted(age_details)

# Compute percentiles
def percentile(data, p):
    if not data:
        return None
    k = (len(data) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(data) else f
    if c == f:
        return data[f]
    return data[f] * (c - k) + data[c] * (k - f)

p10 = percentile(sorted_ages, 10)
p25 = percentile(sorted_ages, 25)
p50 = percentile(sorted_ages, 50)
p75 = percentile(sorted_ages, 75)
p90 = percentile(sorted_ages, 90)
avg_age = sum(age_details) / len(age_details)

# Age top N
top_common_ages = age_counter.most_common(15)

# Year generation labels
generations = {
    "Gen Alpha (2013+)": (2013, 2026),
    "Gen Z (1997-2012)": (1997, 2012),
    "Millennial (1981-1996)": (1981, 1996),
    "Gen X (1965-1980)": (1965, 1980),
    "Boomer (1946-1964)": (1946, 1964),
    "Silent (1928-1945)": (1928, 1945),
    "Greatest (<1928)": (0, 1927),
}

gen_counter = Counter()
for row in rows:
    bd_str = row.get("birth_date", "")
    try:
        year = datetime.strptime(bd_str.strip(), "%Y-%m-%d").date().year
    except:
        continue
    for label, (lo, hi) in generations.items():
        if lo <= year <= hi:
            gen_counter[label] += 1
            break

# ---- BUILD REPORT ----
lines = []
lines.append("# Báo Cáo Phân Tích Độ Tuổi — Birth Chart Database\n")
lines.append(f"**File nguồn:** {INPUT.name}")
lines.append(f"**Số lượng:** {total} bản ghi")
lines.append(f"**Tham chiếu ngày:** {REF_DATE}")
lines.append(f"**Thời gian phân tích:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

lines.append("## 📊 Tổng Quan Thống Kê")
lines.append(f"| Chỉ số | Giá trị |")
lines.append(f"|--------|--------:|")
lines.append(f"| Trung bình tuổi | {avg_age:.1f} |")
lines.append(f"| Median (P50) | {p50:.0f} |")
lines.append(f"| P10 | {p10:.0f} |")
lines.append(f"| P25 | {p25:.0f} |")
lines.append(f"| P75 | {p75:.0f} |")
lines.append(f"| P90 | {p90:.0f} |")
lines.append(f"| Min | {min(age_details)} |")
lines.append(f"| Max | {max(age_details)} |")
lines.append("")

lines.append("## 🧑‍🤝‍🧑 Nhóm Tuổi")
lines.append("| Nhóm | Số lượng | Tỉ lệ |")
lines.append("|------|--------:|------:|")
for label, _, _ in AGE_GROUPS:
    n = group_counter.get(label, 0)
    pct = n / total_with_age * 100
    bar = "█" * int(pct / 2)
    lines.append(f"| {label} | {n:>6} | {pct:>5.1f}% {bar} |")
lines.append("")

lines.append("## 👶👨‍🦳 Thế Hệ (Generation)")
lines.append("| Thế hệ | Số lượng | Tỉ lệ |")
lines.append("|--------|--------:|------:|")
for label, _ in sorted(generations.items(), key=lambda x: -x[1][0]):
    n = gen_counter.get(label, 0)
    pct = n / total_with_age * 100
    bar = "█" * int(pct / 2)
    lines.append(f"| {label} | {n:>6} | {pct:>5.1f}% {bar} |")
lines.append("")

lines.append("## 🔟 Độ Tuổi Phổ Biến Nhất")
lines.append("| Tuổi | Số lượng |")
lines.append("|------|--------:|")
for age, n in top_common_ages:
    lines.append(f"| {age} | {n} |")
lines.append("")

# Write report
report_text = "\n".join(lines)
with open(REPORT, "w", encoding="utf-8") as f:
    f.write(report_text)

print(report_text)
print(f"\n✅ Report: {REPORT}")
