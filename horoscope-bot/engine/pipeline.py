#!/usr/bin/env python3
"""
Votive Academy — Corpus Processing Pipeline (Step 1-4)

Xử lý tài liệu chiêm tinh Vedic:
1. Đồng nhất thuật ngữ
2. Semantic chunking
3. Metadata tagging
4. Embedding index

Usage:
    python3 pipeline.py --source nakshatras
    python3 pipeline.py --source karakatvas
    python3 pipeline.py --source bphs
    python3 pipeline.py --source all
"""

import json
import re
import os
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "corpus" / "raw"
CHUNKS_DIR = BASE_DIR / "corpus" / "chunks"
EMBED_DIR = BASE_DIR / "corpus" / "embeddings"

CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
EMBED_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# TERM STANDARDIZATION
# ──────────────────────────────────────────────

TERM_MAP = {
    "Ascendant": "Lagna",
    "ascendant": "Lagna",
    "1st house": "Nhà 1 (Bản thân)",
    "2nd house": "Nhà 2 (Tài chính)",
    "3rd house": "Nhà 3 (Anh em)",
    "4th house": "Nhà 4 (Gia đình)",
    "5th house": "Nhà 5 (Sáng tạo)",
    "6th house": "Nhà 6 (Sức khỏe)",
    "7th house": "Nhà 7 (Hôn nhân)",
    "8th house": "Nhà 8 (Biến cố)",
    "9th house": "Nhà 9 (May mắn)",
    "10th house": "Nhà 10 (Sự nghiệp)",
    "11th house": "Nhà 11 (Lợi nhuận)",
    "12th house": "Nhà 12 (Ẩn dật)",
    "conjunction": "Giao hội",
    "sextile": "Lục hợp",
    "square": "Góc Vuông",
    "trine": "Tam hợp",
    "opposition": "Đối đỉnh",
}

NAKSHATRA_MAP = {
    "Ashvini": "Ashvini", "Bharani": "Bharani", "Krittika": "Krittika",
    "Rohini": "Rohini", "Mrigashira": "Mrigashira", "Ardra": "Ardra",
    "Punarvasu": "Punarvasu", "Pushya": "Pushya", "Ashlesha": "Ashlesha",
    "Magha": "Magha", "Purva Phalguni": "Purva Phalguni", "Uttara Phalguni": "Uttara Phalguni",
    "Hasta": "Hasta", "Chitra": "Chitra", "Swati": "Swati",
    "Vishakha": "Vishakha", "Anuradha": "Anuradha", "Jyeshtha": "Jyeshtha",
    "Mula": "Mula", "Purva Ashadha": "Purva Ashadha", "Uttara Ashadha": "Uttara Ashadha",
    "Shravana": "Shravana", "Dhanishta": "Dhanishta", "Shatabhisha": "Shatabhisha",
    "Purva Bhadrapada": "Purva Bhadrapada", "Uttara Bhadrapada": "Uttara Bhadrapada",
    "Revati": "Revati"
}

NAKSHATRA_META = {
    "Ashvini": {"lord": "Ketu", "sign": "Aries", "number": 1},
    "Bharani": {"lord": "Venus", "sign": "Aries", "number": 2},
    "Krittika": {"lord": "Sun", "sign": "Aries/Taurus", "number": 3},
    "Rohini": {"lord": "Moon", "sign": "Taurus", "number": 4},
    "Mrigashira": {"lord": "Mars", "sign": "Taurus/Gemini", "number": 5},
    "Ardra": {"lord": "Rahu", "sign": "Gemini", "number": 6},
    "Punarvasu": {"lord": "Jupiter", "sign": "Gemini/Cancer", "number": 7},
    "Pushya": {"lord": "Saturn", "sign": "Cancer", "number": 8},
    "Ashlesha": {"lord": "Mercury", "sign": "Cancer", "number": 9},
    "Magha": {"lord": "Ketu", "sign": "Leo", "number": 10},
    "Purva Phalguni": {"lord": "Venus", "sign": "Leo", "number": 11},
    "Uttara Phalguni": {"lord": "Sun", "sign": "Leo/Virgo", "number": 12},
    "Hasta": {"lord": "Moon", "sign": "Virgo", "number": 13},
    "Chitra": {"lord": "Mars", "sign": "Virgo/Libra", "number": 14},
    "Swati": {"lord": "Rahu", "sign": "Libra", "number": 15},
    "Vishakha": {"lord": "Jupiter", "sign": "Libra/Scorpio", "number": 16},
    "Anuradha": {"lord": "Saturn", "sign": "Scorpio", "number": 17},
    "Jyeshtha": {"lord": "Mercury", "sign": "Scorpio", "number": 18},
    "Mula": {"lord": "Ketu", "sign": "Sagittarius", "number": 19},
    "Purva Ashadha": {"lord": "Venus", "sign": "Sagittarius", "number": 20},
    "Uttara Ashadha": {"lord": "Sun", "sign": "Sagittarius/Capricorn", "number": 21},
    "Shravana": {"lord": "Moon", "sign": "Capricorn", "number": 22},
    "Dhanishta": {"lord": "Mars", "sign": "Capricorn/Aquarius", "number": 23},
    "Shatabhisha": {"lord": "Rahu", "sign": "Aquarius", "number": 24},
    "Purva Bhadrapada": {"lord": "Jupiter", "sign": "Aquarius/Pisces", "number": 25},
    "Uttara Bhadrapada": {"lord": "Saturn", "sign": "Pisces", "number": 26},
    "Revati": {"lord": "Mercury", "sign": "Pisces", "number": 27},
}

# Degree ranges for each nakshatra (key identifiers)
NAKSHATRA_RANGES = [
    ("Ashvini", "00000' Aries - 13o20' Aries"),
    ("Bharani", "13020' Aries - 26o40' Aries"),
    ("Krittika", "26 Aries"),  # unique fragment
    ("Rohini", "10000' Taurus - 23020' Taurus"),
    ("Mrigashira", ""), # hard to detect
    ("Ardra", "6040' Gemini - 20000'Gemini"),
    ("Punarvasu", "20000' Gemini - 3020' Cancer"),
    ("Pushya", "Gncer - 16o40' Cancer"),
    ("Ashlesha", "16040' Cancer - 30000'Cancer"),
    ("Magha", "Leo - 13020' Leo"),
    ("Purva Phalguni", "13020'Leo - 26040' Leo"),
    ("Uttara Phalguni", "26040' Leo - 10o00' Virgo"),
    ("Hasta", "10000' Virgo - 23020' Virgo"),
    ("Chitra", ""),
    ("Swati", "6040' Libra - 20o00' Libra"),
    ("Vishakha", "20000' Libra - 3020' Scorpio"),
    ("Anuradha", "Scorpio"),
    ("Jyeshtha", ""),
    ("Mula", "Sagittarius"),
    ("Purva Ashadha", "13020' Sagittarius"),
    ("Uttara Ashadha", "2604o' Sagittarfls"),
    ("Shravana", "26040' Sagittarfls - 10000' Capricorn"),
    ("Dhanishta", "23020' Capricorn - 6040' Aquarius"),
    ("Shatabhisha", "6040' Aquarius - 20000' Aquarius"),
    ("Purva Bhadrapada", "20000'Aquarius"),
    ("Uttara Bhadrapada", ""),
    ("Revati", "16040' Pisces - 30000' Pisces"),
]

# Subheadings within each nakshatra chapter
NAKSHATRA_SECTIONS = [
    "Sky", "Name", "Symbol", "Deity", "Nature", "Function",
    "Places", "Guna", "Tattwa", "Gana", "Pada", "Quarter",
    "Profession", "Career", "Compatibility", "Marriage",
    "Sexual", "Animal", "Lunar", "Month", "Day",
    "Auspicious", "Inauspicious", "Orientation", "Disposition",
    "Quality", "Activity", "Appearance", "Character",
    "Personality", "Remedy", "Mythology", "Legend",
    "Caste", "Gender", "Dosha", "Element", "Direction",
    "Yoni", "Bird", "Tree",
]


def standardize_text(text, source_lang="en"):
    """Step 1: Đồng nhất thuật ngữ."""
    result = text
    for old, new in sorted(TERM_MAP.items(), key=lambda x: -len(x[0])):
        result = re.sub(r'\b' + re.escape(old) + r'\b', new, result, flags=re.IGNORECASE)
    return result


def find_nakshatra_line(text):
    """Find the best matching nakshatra name for a line of text."""
    text_lower = text.lower()
    for nak_name in NAKSHATRA_MAP:
        if nak_name.lower() in text_lower:
            return nak_name
    return None


# ──────────────────────────────────────────────
# NAKSHATRA CHUNKING (page-break based)
# ──────────────────────────────────────────────

def extract_nakshatras():
    """
    Chunk nakshatras by:
    1. Find chapter boundaries using degree-range markers
    2. Split each chapter into subsections
    3. Tag with metadata
    """
    src = RAW_DIR / "book-of-naksatras.txt"
    if not src.exists():
        print("❌ Nakshatras text not found")
        return []

    text = src.read_text(encoding="utf-8")
    pages = text.split('\n---PAGE BREAK---\n')
    print(f"📄 {len(pages)} pages loaded")

    # Find chapter start pages using degree ranges
    nakshatra_pages = {}  # nakshatra_name -> page_index
    for pg_idx, page_text in enumerate(pages):
        first_500 = page_text[:500].replace('\n', ' ')
        for nk_name, degree_range in NAKSHATRA_RANGES:
            if degree_range and degree_range in first_500:
                if nk_name not in nakshatra_pages:
                    nakshatra_pages[nk_name] = pg_idx
                    print(f"  📍 {nk_name} → page {pg_idx+1}")
                break

    # Also detect by number + nakshatra name
    nak_names = sorted(NAKSHATRA_MAP.keys(), key=lambda x: -len(x))
    for pg_idx, page_text in enumerate(pages):
        first_lines = page_text.split('\n')[:3]
        combined = ' '.join(first_lines)
        # Check for pattern: number on one line, nakshatra name nearby
        for nk_name in nak_names:
            if nk_name.lower() in combined.lower():
                if nk_name not in nakshatra_pages:
                    nakshatra_pages[nk_name] = pg_idx
                    print(f"  📍 {nk_name} → page {pg_idx+1} (alt detection)")
                    break
    
    # Sort by page number
    sorted_naks = sorted(nakshatra_pages.items(), key=lambda x: x[1])
    
    pdfs = []
    for i, (nk_name, start_page) in enumerate(sorted_naks):
        end_page = sorted_naks[i+1][1] if i+1 < len(sorted_naks) else len(pages)
        # Collect all pages for this nakshatra
        section_pages = pages[start_page:end_page]
        full_text = '\n\n'.join(section_pages)
        pdfs.append((nk_name, full_text, start_page, end_page))
    
    print(f"✅ Found {len(pdfs)} nakshatra chapters")

    # Split each nakshatra into sub-sections
    chunks = []
    for nk_name, full_text, start_pg, end_pg in pdfs:
        # Clean text
        cleaned = clean_text(full_text)
        
        # Split by subheadings
        sub_chunks = split_by_subheadings(cleaned, nk_name)
        
        meta = NAKSHATRA_META.get(nk_name, {})
        base_meta = {
            "type": "nakshatra",
            "name": nk_name,
            "number": meta.get("number", 0),
            "lord": meta.get("lord", ""),
            "sign": meta.get("sign", ""),
            "source": "book-of-naksatras",
            "pages": f"{start_pg+1}-{end_pg}",
        }
        
        for sub in sub_chunks:
            chunk_meta = {**base_meta, **sub["metadata"]}
            chunk_id = hashlib.md5(sub["text"][:80].encode()).hexdigest()[:12]
            chunks.append({
                "id": f"nak_{nk_name.lower()}_{chunk_id}",
                "text": standardize_text(sub["text"]),
                "metadata": chunk_meta,
                "char_count": len(sub["text"]),
            })
        
        print(f"  {nk_name}: {len(sub_chunks)} chunks (pages {start_pg+1}-{end_pg})")
    
    print(f"\n✅ Total: {len(chunks)} nakshatra chunks")
    return chunks


def clean_text(text):
    """Clean up OCR artifacts."""
    # Remove page numbers (isolated numbers on their own line)
    text = re.sub(r'\n\d{1,3}\n', '\n', text)
    # Remove header debris
    text = re.sub(r'\n---PAGE BREAK---\n', '\n', text)
    # Normalize multiple spaces
    text = re.sub(r' +', ' ', text)
    return text.strip()


def split_by_subheadings(text, nk_name):
    """Split nakshatra text into semantic chunks using subheadings."""
    lines = text.split('\n')
    chunks = []
    current_section = "Sơ lược"
    current_lines = []
    
    section_headings = [
        "In the Sky", "Name", "Symbol", "Deity", "Nature", 
        "Functioning", "Places", "Guna", "Tattwa", "Gana",
        "Pada", "Quarter", "Profession", "Career", 
        "Compatibility", "Marriage", "Sexual", "Animal",
        "Lunar Month", "Day", "Auspicious", "Inauspicious",
        "Orientation", "Disposition", "Level", "Moveable",
        "Active", "Passive", "Balanced", "Rajasic", "Sattwic",
        "Tamasic", "Female", "Male", "Upward", "Downward",
        "Yoni", "Bird", "Tree", "Caste", "Gender", "Dosha",
        "Element", "Direction", "God", "Remedy", "Mythology",
        "Legend", "Personality", "Appearance", "Character",
        "Temperament", "Health", "Vocation", "Other",
    ]
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Check if this line is a section heading
        is_heading = False
        matched_heading = None
        for heading in section_headings:
            # Match 'heading:' or 'Heading   :' patterns
            if stripped.lower().startswith(heading.lower() + " :") or \
               stripped.lower().startswith(heading.lower() + ":") or \
               stripped.lower() == heading.lower() + ":" or \
               stripped.lower() == heading.lower():
                is_heading = True
                matched_heading = heading
                break
        
        if is_heading and current_lines:
            # Save previous section
            sec_text = '\n'.join(current_lines).strip()
            if len(sec_text) > 50:
                chunks.append({
                    "text": sec_text,
                    "metadata": {
                        "section": current_section,
                        "subtype": "subsection",
                    }
                })
            current_section = matched_heading
            current_lines = []
        elif not is_heading and len(stripped) > 2:
            current_lines.append(stripped)
    
    # Last section
    if current_lines:
        sec_text = '\n'.join(current_lines).strip()
        if len(sec_text) > 50:
            chunks.append({
                "text": sec_text,
                "metadata": {
                    "section": current_section,
                    "subtype": "subsection",
                }
            })
    
    # If no subsections were split, create one big chunk
    if not chunks:
        chunks.append({
            "text": text,
            "metadata": {
                "section": "full",
                "subtype": "full_chapter",
            }
        })
    
    return chunks


# ──────────────────────────────────────────────
# KARAKATVAS CHUNKING
# ──────────────────────────────────────────────

def extract_karakatvas():
    """Chunk Karakatvas by chapter/planet."""
    src = RAW_DIR / "karakatvas.txt"
    if not src.exists():
        print("❌ Karakatvas text not found")
        return []
    
    text = src.read_text(encoding="utf-8")
    pages = text.split('\n---PAGE BREAK---\n')
    print(f"📄 {len(pages)} pages loaded")
    
    # Find chapter starts based on page headings
    karaka_keywords = [
        "Sūrya", "Chandra", "Maṅgala", "Budha", "Guru", "Śukra", "Śani",
        "Rāhu", "Ketu", "Bhāva", "Kāraka", "House", "Bhava",
    ]
    
    chunks = []
    current_heading = None
    current_text = []
    current_pages = []
    
    for pg_idx, page_text in enumerate(pages):
        first_300 = page_text[:300].replace('\n---PAGE BREAK---\n', ' ')
        
        # Check for heading at page start
        heading = None
        for kw in karaka_keywords:
            # Check if keyword appears in first line
            first_lines = [l.strip() for l in page_text.split('\n')[:5] if l.strip()]
            for l in first_lines:
                if kw.lower() in l.lower() and len(l) < 80:
                    heading = l[:60]
                    break
            if heading:
                break
        
        if heading and current_text:
            # Save previous section
            content = '\n'.join(current_text).strip()
            if len(content) > 300:
                chunks.append({
                    "text": standardize_text(content),
                    "metadata": {
                        "type": "karaka",
                        "heading": current_heading,
                        "source": "karakatvas",
                        "pages": f"{current_pages[0]+1}-{current_pages[-1]+1}",
                        "char_count": len(content),
                    }
                })
            current_text = []
            current_pages = []
        
        if heading:
            current_heading = heading
        
        current_text.append(page_text)
        current_pages.append(pg_idx)
    
    # Last section
    if current_text:
        content = '\n'.join(current_text).strip()
        if len(content) > 300:
            chunks.append({
                "text": standardize_text(content),
                "metadata": {
                    "type": "karaka",
                    "heading": current_heading or "appendix",
                    "source": "karakatvas",
                    "pages": f"{current_pages[0]+1}-{current_pages[-1]+1}",
                    "char_count": len(content),
                }
            })
    
    print(f"✅ Karakatvas: {len(chunks)} chunks")
    return chunks


# ──────────────────────────────────────────────
# BPHS EXTRACTION
# ──────────────────────────────────────────────

def extract_bphs():
    """Extract BPHS using pdftotext or page rendering."""
    src = RAW_DIR / "Brihat Parasara Hora Sastra with English Translation Girish Chand Sharma Volume 1.pdf"
    txt_src = RAW_DIR / "bphs_vol1.txt"
    
    if not txt_src.exists():
        print("⏳ Running pdftotext...")
        import subprocess
        result = subprocess.run(
            ["pdftotext", "-layout", str(src), str(txt_src)],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode == 0 and txt_src.exists():
            print(f"✅ pdftotext OK: {txt_src.stat().st_size:,} bytes")
        else:
            print(f"❌ pdftotext failed: {result.stderr[:200]}")
            print("⚠️ BPHS has custom font encoding. Skip or OCR later.")
            return []
    
    text = txt_src.read_text(encoding="utf-8", errors="replace")
    print(f"📄 BPHS: {len(text):,} chars")
    
    # Chapter detection
    chunks = []
    chapter_pattern = re.compile(
        r'(Chapter|Adhyāya|Adhyaya|अध्याय)\s*[\.:]?\s*(\d+)\s*[\.\-–—\[\]]*\s*(.*)',
        re.IGNORECASE
    )
    
    lines = text.split('\n')
    current_chapter = None
    current_num = None
    current_lines = []
    
    for line in lines:
        m = chapter_pattern.search(line)
        if m:
            if current_chapter and current_lines:
                content = '\n'.join(current_lines).strip()
                if len(content) > 200:
                    chunks.append({
                        "text": standardize_text(content),
                        "metadata": {
                            "type": "bphs_chapter",
                            "chapter": current_num,
                            "heading": current_chapter.strip(),
                            "source": "BPHS_Vol1",
                            "char_count": len(content),
                        }
                    })
            current_num = int(m.group(2))
            current_chapter = m.group(0)[:80]
            current_lines = [line]
        elif current_chapter:
            current_lines.append(line)
    
    # Last chapter
    if current_chapter and current_lines:
        content = '\n'.join(current_lines).strip()
        if len(content) > 200:
            chunks.append({
                "text": standardize_text(content),
                "metadata": {
                    "type": "bphs_chapter",
                    "chapter": current_num,
                    "heading": current_chapter.strip(),
                    "source": "BPHS_Vol1",
                    "char_count": len(content),
                }
            })
    
    print(f"✅ BPHS: {len(chunks)} chapters")
    return chunks


# ──────────────────────────────────────────────
# SAVE & BUILD INDEX
# ──────────────────────────────────────────────

def save_chunks(chunks, name):
    """Save chunks as JSONL."""
    path = CHUNKS_DIR / f"{name}.jsonl"
    with open(path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    print(f"💾 Saved {len(chunks)} chunks → {path}")
    return path


def build_embedding_index():
    """
    Step 4: Build FAISS embedding index from chunks.
    Uses sentence-transformers for embeddings.
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        import faiss
    except ImportError:
        print("⚠️ Skipping embeddings: sentence-transformers/faiss not installed.")
        print("   Run: pip3 install sentence-transformers faiss-cpu")
        return
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    all_chunks = []
    all_metadatas = []
    
    for f in sorted(CHUNKS_DIR.glob("*.jsonl")):
        with open(f) as fh:
            for line in fh:
                chunk = json.loads(line)
                all_chunks.append(chunk)
                all_metadatas.append(chunk["metadata"])
    
    if not all_chunks:
        print("❌ No chunks to embed")
        return
    
    texts = [c["text"] for c in all_chunks]
    print(f"📊 Embedding {len(texts)} chunks...")
    
    embeddings = model.encode(texts, show_progress_bar=True)
    dim = embeddings.shape[1]
    
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings.astype(np.float32))
    
    # Save
    faiss.write_index(index, str(EMBED_DIR / "index.faiss"))
    with open(EMBED_DIR / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump(all_metadatas, f, ensure_ascii=False)
    with open(EMBED_DIR / "id_map.json", 'w') as f:
        json.dump([c["id"] for c in all_chunks], f)
    
    print(f"✅ Index built: {len(embeddings)} chunks, {dim} dimensions")
    print(f"   Index: {EMBED_DIR / 'index.faiss'}")


# ──────────────────────────────────────────────
# RUN
# ──────────────────────────────────────────────

def run(source="all"):
    print("=" * 60)
    print("🔮 VOTIVE ACADEMY — Corpus Processing Pipeline")
    print("=" * 60)
    
    total = 0
    
    if source in ("nakshatras", "all"):
        print("\n📖 [NAKSHATRAS]")
        chunks = extract_nakshatras()
        if chunks:
            save_chunks(chunks, "nakshatras")
            total += len(chunks)
    
    if source in ("karakatvas", "all"):
        print("\n📖 [KARAKATVAS]")
        chunks = extract_karakatvas()
        if chunks:
            save_chunks(chunks, "karakatvas")
            total += len(chunks)
    
    if source in ("bphs", "all"):
        print("\n📖 [BPHS VOL 1]")
        chunks = extract_bphs()
        if chunks:
            save_chunks(chunks, "bphs_vol1")
            total += len(chunks)
    
    print(f"\n{'='*60}")
    print(f"✅ TOTAL: {total} chunks processed")
    print(f"📁 Chunks: {CHUNKS_DIR}/")
    
    # Build embedding index if chunks exist
    if total > 0:
        print("\n📊 Building embedding index...")
        build_embedding_index()
    
    print(f"{'='*60}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Votive Corpus Pipeline")
    parser.add_argument("--source", choices=["nakshatras", "karakatvas", "bphs", "all"],
                        default="all")
    args = parser.parse_args()
    run(args.source)
