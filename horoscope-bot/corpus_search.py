#!/usr/bin/env python3
"""
YouTube Content Research — Search horoscope-bot corpus for topic ideas
Usage:
    python3 corpus_search.py "Jupiter ingress Cancer" --max 5
    python3 corpus_search.py "Moon Nakshatra Ashwini" --source nakshatras
    python3 corpus_search.py "Saturn aspect" --max 10 --json
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
CHUNKS_DIR = BASE_DIR / "corpus" / "chunks"

def load_all_chunks():
    chunks = []
    for f in sorted(CHUNKS_DIR.glob("*.jsonl")):
        source = f.stem
        with open(f) as fh:
            for line in fh:
                if line.strip():
                    item = json.loads(line)
                    item["_source_file"] = source
                    chunks.append(item)
    return chunks

def search(chunks, query, max_results=5, source_filter=None):
    """Keyword search across all chunks."""
    terms = query.lower().split()
    scored = []
    
    for chunk in chunks:
        if source_filter and chunk["_source_file"] != source_filter:
            continue
        
        text = chunk.get("text", "").lower()
        meta = json.dumps(chunk.get("metadata", {})).lower()
        searchable = text + " " + meta
        
        score = sum(1 for t in terms if t in searchable)
        # Bonus for title/heading matches
        heading = chunk.get("metadata", {}).get("heading", "").lower() + \
                  chunk.get("metadata", {}).get("name", "").lower()
        heading_score = sum(2 for t in terms if t in heading)
        
        total = score + heading_score
        if total > 0:
            scored.append((total, chunk))
    
    scored.sort(key=lambda x: -x[0])
    return scored[:max_results]

def format_chunk(chunk, score):
    meta = chunk.get("metadata", {})
    source = chunk["_source_file"]
    name = meta.get("name", meta.get("heading", meta.get("planet", "—")))
    chunk_type = meta.get("type", "—")
    
    lines = [
        f"━━━ [{source}] {chunk_type}: {name} (score: {score}) ━━━",
        chunk.get("text", "")[:800],
        ""
    ]
    return "\n".join(lines)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Search Vedic astrology corpus for YouTube content")
    parser.add_argument("query", nargs="+", help="Search terms")
    parser.add_argument("--max", type=int, default=5, help="Max results")
    parser.add_argument("--source", help="Filter by source (nakshatras, karakatvas, bphs_vol1, etc.)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--list-sources", action="store_true", help="List available sources")
    args = parser.parse_args()
    
    if args.list_sources:
        print("Available sources:")
        for f in sorted(CHUNKS_DIR.glob("*.jsonl")):
            count = sum(1 for _ in open(f))
            print(f"  {f.stem}: {count} chunks")
        sys.exit(0)
    
    query = " ".join(args.query)
    print(f"🔍 Searching corpus for: \"{query}\"\n")
    
    chunks = load_all_chunks()
    print(f"📚 Corpus: {len(chunks)} chunks across {len(list(CHUNKS_DIR.glob('*.jsonl')))} sources\n")
    
    results = search(chunks, query, args.max, args.source)
    
    if args.json:
        output = [{
            "score": s,
            "source": c["_source_file"],
            "metadata": c["metadata"],
            "text": c["text"][:800]
        } for s, c in results]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"📌 Found {len(results)} relevant chunks:\n")
        for score, chunk in results:
            print(format_chunk(chunk, score))
