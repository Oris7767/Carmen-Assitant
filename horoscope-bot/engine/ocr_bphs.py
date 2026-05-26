#!/usr/bin/env python3
"""
OCR Pipeline for BPHS Vol 1
- PDF has custom font encoding (GlyphlessFont) -> text extraction fails
- Solution: render pages as images -> tesseract OCR -> extract English

Usage:
    python3 ocr_bphs.py                     # full run (657 pages)
    python3 ocr_bphs.py --pages 1-50        # test first 50 pages
    python3 ocr_bphs.py --resume            # resume from checkpoint
"""

import os
import sys
import time
import json
import subprocess
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "corpus" / "raw"
OCR_DIR = BASE_DIR / "corpus" / "raw" / "ocr_bphs"
TEXT_DIR = BASE_DIR / "corpus" / "raw"

OCR_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = RAW_DIR / "Brihat Parasara Hora Sastra with English Translation Girish Chand Sharma Volume 1.pdf"
CHECKPOINT = OCR_DIR / "checkpoint.json"


def get_page_count():
    import fitz
    doc = fitz.open(str(PDF_PATH))
    n = doc.page_count
    doc.close()
    return n


def render_and_ocr(pages=None, dpi=150, resume=False):
    import fitz
    
    doc = fitz.open(str(PDF_PATH))
    total_pages = doc.page_count
    
    completed = set()
    if resume and CHECKPOINT.exists():
        completed = set(json.loads(CHECKPOINT.read_text()))
        print(f"📌 Resuming: {len(completed)} pages done")
    
    if pages:
        page_range = pages
    else:
        page_range = range(total_pages)
    
    all_text = []
    start_time = time.time()
    
    for pg_idx in page_range:
        if pg_idx in completed:
            continue
        
        page = doc[pg_idx]
        pix = page.get_pixmap(dpi=dpi)
        img_path = OCR_DIR / f"page_{pg_idx+1:04d}.png"
        pix.save(str(img_path))
        
        txt_path = OCR_DIR / f"page_{pg_idx+1:04d}"
        low_img = None
        
        try:
            subprocess.run(
                ["tesseract", str(img_path), str(txt_path), "-l", "eng", "--psm", "6"],
                capture_output=True, timeout=60
            )
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ Page {pg_idx+1} timeout, retrying 100 DPI...")
            pix2 = page.get_pixmap(dpi=100)
            low_img = OCR_DIR / f"page_{pg_idx+1:04d}_low.png"
            pix2.save(str(low_img))
            subprocess.run(
                ["tesseract", str(low_img), str(txt_path), "-l", "eng", "--psm", "6"],
                capture_output=True, timeout=60
            )
        
        # Read OCR result
        ocr_file = txt_path.with_suffix('.txt')
        if ocr_file.exists():
            with open(ocr_file, 'rb') as f:
                raw = f.read()
            page_text = raw.decode('utf-8', errors='replace')
            all_text.append(f"\n---PAGE {pg_idx+1}---\n{page_text}")
        else:
            all_text.append(f"\n---PAGE {pg_idx+1}---\n[BLANK]\n")
        
        # Clean up
        img_path.unlink(missing_ok=True)
        if low_img:
            low_img.unlink(missing_ok=True)
        if ocr_file.exists():
            ocr_file.unlink()
        
        completed.add(pg_idx)
        if (pg_idx + 1) % 10 == 0 or pg_idx == page_range[-1]:
            elapsed = time.time() - start_time
            rate = (pg_idx + 1 - list(completed).index(min(page_range)) if completed else 1) / max(elapsed, 1)
            remaining = (total_pages - pg_idx - 1) / max(rate, 0.01)
            print(f"  📄 Page {pg_idx+1}/{total_pages} ({rate:.1f} pg/s, ETA: {remaining/60:.0f}m)", flush=True)
        
        if (pg_idx + 1) % 20 == 0:
            CHECKPOINT.write_text(json.dumps(sorted(completed)))
    
    doc.close()
    CHECKPOINT.write_text(json.dumps(sorted(completed)))
    return ''.join(all_text)


def filter_english(text):
    pages = text.split('\n---PAGE ')
    filtered = []
    
    for entry in pages:
        if not entry.strip():
            continue
        lines = entry.split('\n')
        header = lines[0] if lines else ''
        num = re.search(r'(\d+)', header)
        page_num = num.group(1) if num else '?'
        content = '\n'.join(lines[1:]) if len(lines) > 1 else ''
        
        total = len(content.strip())
        if total == 0:
            continue
        
        latin = sum(1 for c in content if c.isascii() and c.isalpha())
        deva = sum(1 for c in content if '\u0900' <= c <= '\u097F')
        ratio = latin / total if total > 0 else 0
        
        if ratio > 0.2:
            filtered.append(f"\n---PAGE {page_num}---\n{content.strip()}")
        else:
            print(f"  🚫 Page {page_num}: {ratio:.0%} Latin, {deva} Devanagari")
    
    return ''.join(filtered)


def detect_chapters(text):
    pattern = re.compile(
        r'(Chapter|Adhyāya|Adhyaya|अध्याय)\s*[\.:]?\s*(\d+)\s*[\.\-–—\[\]]*\s*(.*)',
        re.IGNORECASE
    )
    lines = text.split('\n')
    chapters = []
    for line in lines:
        m = pattern.search(line)
        if m:
            chapters.append((int(m.group(2)), m.group(0)[:100].strip()))
    return chapters


def run(pages=None, dpi=150, resume=False, filter_only=False):
    print("=" * 60)
    print("🔮 BPHS OCR Pipeline")
    print("=" * 60)
    
    total = get_page_count()
    print(f"📄 Total: {total} pages")
    
    if filter_only:
        output = TEXT_DIR / "bphs_ocr_raw.txt"
        text = output.read_text(encoding="utf-8", errors="replace") if output.exists() else ""
        if not text:
            print("❌ No OCR output found")
            return
    else:
        if pages and isinstance(pages, str) and '-' in pages:
            parts = pages.split('-')
            pages = range(int(parts[0]) - 1, int(parts[1]))
        
        print(f"\n🔍 OCR (dpi={dpi})...")
        text = render_and_ocr(pages, dpi, resume)
        
        output = TEXT_DIR / "bphs_ocr_raw.txt"
        output.write_text(text, encoding="utf-8")
        print(f"💾 Raw: {output} ({len(text):,} chars)")
    
    print(f"\n🔍 Filtering English...")
    english = filter_english(text)
    
    eng_file = TEXT_DIR / "bphs_ocr_english.txt"
    eng_file.write_text(english, encoding="utf-8")
    print(f"💾 English: {eng_file} ({len(english):,} chars, {len(english)*100//max(len(text),1)}%)")
    
    chapters = detect_chapters(english)
    if chapters:
        print(f"\n📑 {len(chapters)} chapters:")
        for num, title in chapters[:20]:
            print(f"  Ch.{num}: {title}")
        if len(chapters) > 20:
            print(f"  ... +{len(chapters)-20}")
    
    print("\n✅ Done")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", help="e.g. '1-50'")
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--filter-only", action="store_true")
    args = parser.parse_args()
    run(args.pages, args.dpi, args.resume, args.filter_only)
