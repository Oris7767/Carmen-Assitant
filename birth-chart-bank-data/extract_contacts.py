#!/usr/bin/env python3
"""
Extract name + email from clean birth chart CSV into a separate contacts CSV.
Loại bỏ email trùng lặp.
"""

import csv
from pathlib import Path
from collections import Counter

INPUT = Path(__file__).parent / "birth_chart_clean.csv"
OUTPUT = Path(__file__).parent / "birth_chart_contacts.csv"

with open(INPUT, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

contacts = []
seen_emails = set()
dup_emails = []
name_blank = 0
email_blank = 0
both_blank = 0

for row in rows:
    name = row.get("name", "").strip()
    email = row.get("email", "").strip()

    if not name and not email:
        both_blank += 1
        continue

    # Dedup by email (if email exists)
    if email:
        norm_email = email.lower()
        if norm_email in seen_emails:
            dup_emails.append(email)
            continue
        seen_emails.add(norm_email)

    contacts.append({"name": name, "email": email})
    if not name:
        name_blank += 1
    if not email:
        email_blank += 1

with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "email"])
    writer.writeheader()
    writer.writerows(contacts)

total = len(contacts)
has_name = total - name_blank
has_email = total - email_blank

print(f"✅ Contacts extracted: {OUTPUT}")
print(f"   Total entries: {total}")
print(f"   Have name: {has_name}")
print(f"   Have email: {has_email}")
print(f"   Duplicate emails removed: {len(dup_emails)}")
print(f"   Neither name nor email (skipped): {both_blank}")

# Show most frequent duplicate emails
if dup_emails:
    dup_counts = Counter(dup_emails)
    print(f"\n📌 Top emails bị trùng nhiều nhất:")
    for email, count in dup_counts.most_common(10):
        print(f"   {email} — {count+1} lần")
