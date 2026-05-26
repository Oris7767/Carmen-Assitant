#!/usr/bin/env python3
"""
Embedding index builder + semantic search via Gemini Embedding API.
No local ML dependencies needed — uses Google's embedding API.

Usage:
    python3 embeddings.py --build          # Build FAISS index from chunks
    python3 embeddings.py --search "text"  # Semantic search
"""

import json
import os
import sys
import numpy as np
import faiss
import re
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHUNKS_DIR = BASE_DIR / "corpus" / "chunks"
EMBED_DIR = BASE_DIR / "corpus" / "embeddings"
EMBED_DIR.mkdir(parents=True, exist_ok=True)

# Gemini embedding config
EMBEDDING_MODEL = "models/gemini-embedding-2"
EMBEDDING_DIM = 3072  # gemini-embedding-2 output dimension


def get_client():
    """Get Gemini API client."""
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text().split('\n'):
                line = line.strip()
                if 'GEMINI_API_KEY' in line:
                    api_key = line.split('=', 1)[1].strip()
    if not api_key:
        raise ValueError("No GEMINI_API_KEY found. Set env var or add to .env")
    return genai.Client(api_key=api_key)


def load_all_chunks():
    """Load all chunks from JSONL files."""
    chunks = []
    for f in sorted(CHUNKS_DIR.glob("*.jsonl")):
        with open(f) as fh:
            for line in fh:
                if line.strip():
                    chunks.append(json.loads(line))
    return chunks


def embed_texts(client, texts, batch_size=1):
    """Embed texts one at a time. Gemini API batch returns 1 embed per Content object,
    but sequential calls are more reliable with rate limiting."""
    from google.genai import types
    import httpx
    
    all_embeddings = []
    total = len(texts)
    
    for i, text in enumerate(texts):
        content = types.Content(parts=[types.Part(text=text)])
        
        success = False
        for attempt in range(5):
            try:
                result = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=[content],
                    config=types.EmbedContentConfig(
                        http_options=types.HttpOptions(timeout=30_000),
                    ),
                )
                all_embeddings.append(result.embeddings[0].values)
                success = True
                if (i+1) % 10 == 0 or i+1 == total:
                    print(f"  ⚡ Embedded {i+1}/{total}")
                    sys.stdout.flush()
                break
            except Exception as e:
                if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
                    wait = 15 * (attempt + 1)
                    print(f"\n  ⏳ Rate limited at {i+1}/{total}, wait {wait}s...")
                    sys.stdout.flush()
                    time.sleep(wait)
                elif 'timeout' in str(e).lower() or 'deadline' in str(e).lower():
                    print(f"\n  ⏱ Timeout at {i+1}/{total}, retrying...")
                    time.sleep(5)
                else:
                    print(f"\n  ⚠️ Error at {i+1}/{total}: {str(e)[:80]}")
                    time.sleep(5)
        
        if not success:
            print(f"  ❌ Failed #{i+1}, using zero vector")
            all_embeddings.append([0.0] * EMBEDDING_DIM)
        
        if (i+1) % 20 == 0:
            time.sleep(2)  # cool-down every 20
    
    print()
    return np.array(all_embeddings, dtype=np.float32)


def build_index():
    """Build FAISS index from all chunks."""
    print("=" * 60)
    print("📊 BUILDING EMBEDDING INDEX")
    print("=" * 60)
    
    chunks = load_all_chunks()
    print(f"📚 Loaded {len(chunks)} chunks")
    
    if not chunks:
        print("❌ No chunks found!")
        return
    
    client = get_client()
    
    # Prepare texts for embedding
    texts = []
    for c in chunks:
        # Combine text + metadata for better embedding
        meta = c["metadata"]
        prefix = ""
        if meta.get("name"):
            prefix = f"{meta['name']}: "
        elif meta.get("heading"):
            prefix = f"{meta['heading']}: "
        elif meta.get("planet"):
            prefix = f"{meta['planet']}: "
        texts.append(prefix + c["text"][:1000])  # Truncate to fit token limits
    
    print(f"🧠 Embedding {len(texts)} texts via Gemini ({EMBEDDING_MODEL})...")
    embeddings = embed_texts(client, texts)
    
    dim = embeddings.shape[1]
    print(f"📐 Embedding dimension: {dim}")
    
    # Build FAISS index
    index = faiss.IndexFlatIP(dim)  # Inner product = cosine similarity for normalized vectors
    # Normalize for cosine similarity (skip zero vectors to avoid NaN)
    zero_mask = np.all(np.abs(embeddings) < 1e-10, axis=1)
    if np.any(zero_mask):
        print(f"  ⚠️ {np.sum(zero_mask)} zero vectors detected, replacing with small random")
        # Replace zeros with small random values so normalization works
        np.random.seed(42)
        embeddings[zero_mask] = np.random.randn(np.sum(zero_mask), dim) * 0.001
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    
    # Save
    faiss.write_index(index, str(EMBED_DIR / "index.faiss"))
    with open(EMBED_DIR / "metadata.json", 'w', encoding='utf-8') as f:
        json.dump([c["metadata"] for c in chunks], f, ensure_ascii=False)
    # Generate IDs for chunks that don't have them
    chunk_ids = []
    for c in chunks:
        if "id" in c and c["id"]:
            chunk_ids.append(c["id"])
        else:
            import hashlib
            cid = hashlib.md5(c["text"][:80].encode()).hexdigest()[:12]
            chunk_ids.append(f"chunk_{cid}")
    with open(EMBED_DIR / "id_map.json", 'w', encoding='utf-8') as f:
        json.dump(chunk_ids, f, ensure_ascii=False)
    with open(EMBED_DIR / "chunks.json", 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, indent=1)
    
    print(f"\n✅ Index built: {len(chunks)} chunks, {dim} dim")
    print(f"   Index: {EMBED_DIR / 'index.faiss'}")


def search(query, k=15):
    """Search FAISS index with a query string."""
    index_path = EMBED_DIR / "index.faiss"
    meta_path = EMBED_DIR / "metadata.json"
    chunks_path = EMBED_DIR / "chunks.json"
    
    if not index_path.exists():
        raise FileNotFoundError("No index found. Run `python3 embeddings.py --build` first")
    
    index = faiss.read_index(str(index_path))
    with open(meta_path) as f:
        metadatas = json.load(f)
    with open(chunks_path) as f:
        chunks = json.load(f)
    
    client = get_client()
    
    # Embed query
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[query],
    )
    query_vec = np.array([result.embeddings[0].values], dtype=np.float32)
    faiss.normalize_L2(query_vec)
    
    # Search
    scores, indices = index.search(query_vec, k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        if idx >= 0 and idx < len(chunks):
            results.append({
                "chunk": chunks[idx],
                "metadata": metadatas[idx],
                "score": float(scores[0][i]),
            })
    
    return results


def search_by_chart(chart_data, k=10):
    """
    Search for relevant chunks based on chart data.
    Generates multiple queries from chart elements and combines results.
    """
    queries = []
    
    # Query by Lagna nakshatra
    asc = chart_data.get("ascendant", {})
    nak = asc.get("nakshatra", {})
    if nak:
        queries.append(f"{nak['name']} nakshatra characteristics personality {nak['lord']} pada {nak.get('pada', 1)}")
    
    # Query by Lagna sign
    sign = asc.get("sign", {})
    if sign:
        queries.append(f"{sign['name']} ascendant lagna personality traits characteristics")
    
    # Query by each planet's sign + house + nakshatra
    for p in chart_data.get("planets", []):
        pname = p.get("planet", "")
        psign = p.get("sign", {}).get("name", "")
        phouse = p.get("house", {}).get("number", "")
        pnak = p.get("nakshatra", {}).get("name", "")
        plord = p.get("nakshatra", {}).get("lord", "")
        
        if pname in ("URANUS", "NEPTUNE", "PLUTO"):
            continue  # Skip outer planets for Vedic focus
            
        if pnak:
            queries.append(f"{pnak} nakshatra {pname} planet characteristics")
        if psign and phouse:
            queries.append(f"{pname} in {psign} house {phouse} effects")
    
    # Query by house contents
    for h in chart_data.get("houses", []):
        if h.get("planets"):
            planets_str = " ".join(h["planets"])
            queries.append(f"house {h['number']} {h['sign']} {planets_str} effects")
    
    # Query by aspects
    for p in chart_data.get("planets", []):
        pname = p.get("planet", "")
        if pname in ("URANUS", "NEPTUNE", "PLUTO"):
            continue
        for asp in p.get("aspects", []):
            queries.append(f"{pname} {asp['aspect']} {asp['planet']} aspect effect")
    
    # Query by retrograde planets
    for p in chart_data.get("planets", []):
        if p.get("isRetrograde") and p["planet"] not in ("URANUS", "NEPTUNE", "PLUTO"):
            queries.append(f"{p['planet']} retrograde effect vedic astrology")
    
    # Query by current dasha
    dashas = chart_data.get("dashas", {})
    current = dashas.get("current", {})
    if current:
        queries.append(f"{current['planet']} maha dasha effects characteristics")
    
    # Trim queries (max 15, mix nakshatra + house + aspect + karaka)
    seen = set()
    unique_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)
    # Prioritize: keep nakshatra + karaka queries first
    prio_queries = [q for q in unique_queries if 'nakshatra' in q.lower() or 'karaka' in q.lower() or 'retrograde' in q.lower()]
    other_queries = [q for q in unique_queries if q not in prio_queries]
    unique_queries = (prio_queries + other_queries)[:15]
    
    # Search each query and combine results
    all_results = {}
    for q in unique_queries:
        try:
            results = search(q, k=5)
            for r in results:
                chunk_id = r["chunk"].get("id", "")
                if chunk_id not in all_results or r["score"] > all_results[chunk_id]["score"]:
                    all_results[chunk_id] = r
        except Exception as e:
            print(f"  ⚠️ Search error for '{q[:50]}': {e}")
    
    # Sort by score
    sorted_results = sorted(all_results.values(), key=lambda x: -x["score"])
    # Return at least k results, but also include any with score > 0.6
    min_results = max(k, sum(1 for r in sorted_results if r["score"] > 0.6))
    return sorted_results[:min_results]


def keyword_search(chart_data, chunks=None):
    """Fallback: keyword-based search using metadata matching."""
    if chunks is None:
        chunks = load_all_chunks()
    
    planets_data = {p["planet"]: p for p in chart_data.get("planets", [])}
    houses_data = {h["number"]: h for h in chart_data.get("houses", [])}
    asc_nak = chart_data.get("ascendant", {}).get("nakshatra", {}).get("name", "")
    
    matched = []
    
    for chunk in chunks:
        meta = chunk["metadata"]
        score = 0
        reasons = []
        
        # Match nakshatra name in chunk
        if meta.get("type") == "nakshatra" and meta.get("name"):
            chunk_nak = meta["name"].lower()
            # Check if any planet is in this nakshatra
            for pname, pdata in planets_data.items():
                pnak = pdata.get("nakshatra", {}).get("name", "").lower()
                if pnak and chunk_nak in pnak:
                    score += 3
                    reasons.append(f"{pname}={meta['name']}")
            # Check Lagna nakshatra
            if asc_nak.lower() == chunk_nak:
                score += 3
                reasons.append(f"Lagna={meta['name']}")
        
        # Match karaka (planet significations)
        if meta.get("type") == "karaka":
            chunk_planet = meta.get("planet", "").lower()
            chunk_heading = meta.get("heading", "").lower()
            # Direct planet match
            if chunk_planet and any(chunk_planet == p.lower() for p in planets_data):
                score += 3
                reasons.append(f"karaka_{meta['planet']}")
            # Match topics (houses)
            for hnum, hdata in houses_data.items():
                house_labels = {
                    1: "self|personality|appearance|health|body",
                    2: "wealth|finance|family|speech",
                    3: "courage|sibling|communication|short travel",
                    4: "home|mother|comfort|property|education",
                    5: "children|creativity|speculation|intelligence",
                    6: "health|disease|enemy|service|debt",
                    7: "marriage|partner|relationship|business",
                    8: "longevity|occult|sudden|inheritance",
                    9: "luck|dharma|guru|father|pilgrimage|philosophy",
                    10: "career|profession|status|authority|karma",
                    11: "gain|income|fulfillment|network",
                    12: "loss|expenditure|foreign|spirituality|hospital",
                }
                hlabel = house_labels.get(hnum, "")
                for kw in hlabel.split("|"):
                    if kw.strip() and kw.strip() in chunk_heading:
                        score += 1
                        reasons.append(f"house{hnum}_{kw}")
        
        if score > 0:
            matched.append((score, reasons, chunk))
    
    matched.sort(key=lambda x: -x[0])
    return matched


# ─── CLI ───

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="Build FAISS index")
    parser.add_argument("--search", type=str, help="Search query")
    args = parser.parse_args()
    
    if args.build:
        build_index()
    elif args.search:
        results = search(args.search)
        print(f"\n🔍 Results for: {args.search}\n")
        for r in results[:10]:
            meta = r["metadata"]
            name = meta.get("name", meta.get("heading", meta.get("planet", "?")))
            print(f"  [{r['score']:.3f}] {meta.get('type','?')}/{name}: {r['chunk']['text'][:100]}...")
    else:
        parser.print_help()
