#!/usr/bin/env python3
"""
patreon_post_gen_v2.py — Aether Patreon Post Generator V2 (Format B+)

Uses get_full_report_data() + ReportGenerator.generate_patreon_report() to
output the approved 10-section Format B+ with:
  - Aether AI (Gemini) analysis
  - 4-year historical correlation
  - Macro context (DXY, Fed, news)
  - Multi-TF Technical
  - Risk Matrix (6 types)
  - Forward Outlook 3-7 days
  - Super Cycle Countdown (Quant Score)

Output:
  - patreon-db/patreon-post-content-v3.md   → for patreon_poster.js (auto-draft)
  - patreon-db/patreon_posts/patreon_post_YYYY-MM-DD.md  → archive

Usage:
    python3 patreon_post_gen_v2.py              # today's analysis (default)
    python3 patreon_post_gen_v2.py --tomorrow   # forecast next trading day
"""

import os, sys
from pathlib import Path
from datetime import datetime, timedelta
import pytz

# ── Path setup ──
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (WORKSPACE, os.path.join(WORKSPACE, 'engines')):
    if p not in sys.path:
        sys.path.insert(0, p)

from run_bot import get_full_report_data
from report_generator import ReportGenerator

# ── RAG integration ──
RAG_DIR = Path(WORKSPACE) / "rag-gold"
sys.path.insert(0, str(RAG_DIR))
try:
    from rag_bridge import get_rag_context, format_for_llm
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

TZ = pytz.timezone("Asia/Ho_Chi_Minh")
OUTPUT_DIR = Path(WORKSPACE) / "patreon-db" / "patreon_posts"
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_patreon_content(forecast_tomorrow=False):
    """
    Generate Format B+ Patreon report (10 sections).

    Args:
        forecast_tomorrow: If True, mention next trading day in output.
                           (Data is still latest available — no prediction)

    Returns:
        bool — True on success
    """
    now = datetime.now(TZ)
    date_str = now.strftime("%Y-%m-%d")

    print(f"🪐 Aether — Patreon Content Generator V2 (Format B+)")
    print(f"📅 {date_str} | {'🌤️ Forecast mode' if forecast_tomorrow else '📊 Current analysis'}")
    print()

    # ── Step 1: Get full report data ──
    print("📡 Step 1/3 — Fetching market data + Aether AI...")
    try:
        data = get_full_report_data(include_carmen=True)
    except Exception as e:
        print(f"❌ get_full_report_data failed: {e}")
        print("   Retrying without Aether AI (fallback)...")
        try:
            data = get_full_report_data(include_carmen=False)
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")
            return False

    if data is None or not data:
        print("❌ No data returned")
        return False

    price = data.get('price', 0)
    carmen = data.get('carmen_analysis')
    if carmen and not carmen.get('error'):
        ca = carmen
        print(f"   ✅ Aether AI — Bias: {ca.get('bias', 'N/A')} | Confidence: {ca.get('confidence', 0)*100:.0f}%")
    else:
        print(f"   ⚠️ Aether AI unavailable — using rule-based fallback")
    print(f"   ✅ Price: ${price:.1f} | Gann base: {data.get('gann_base', 'N/A')}")
    print(f"   ✅ Vedic: {len(data.get('vedic_planets', {}))} planets | Hora: {data.get('hora', {}).get('hora', 'N/A')}")

    # ── Step 1b: RAG historical context ──
    rag_context = None
    if RAG_AVAILABLE:
        print()
        print("🔍 Step 1b — Searching RAG for historical patterns...")
        try:
            # Extract astro conditions from data for RAG query
            vedic = data.get('vedic_planets', {})
            
            # Handle both formats: {'Moon': {'sign': 'X'}} or {'MOON': 'X (Y°)'}
            moon_data = vedic.get('Moon', vedic.get('MOON', ''))
            if isinstance(moon_data, dict):
                moon_sign = moon_data.get('sign', '')
                moon_nak = moon_data.get('nakshatra', '')
            elif isinstance(moon_data, str):
                # Parse "Libra (202.71°)" format
                moon_sign = moon_data.split('(')[0].strip() if moon_data else ''
                moon_nak = data.get('astro_report', '')
                # Try to extract nakshatra from astro_report
                import re
                # Try multiple patterns for nakshatra extraction
                astro_str = str(data.get('astro_report', ''))
                nak_match = re.search(r'Nakshatra:\s*(\w+(?:\s+\w+)?)', astro_str)
                if not nak_match:
                    # Pattern: 'Vishakha (chủ tinh Jupiter)'
                    nak_match = re.search(r'(\w+)\s*\(chủ tinh', astro_str)
                if not nak_match:
                    # Pattern from correlation log
                    nak_match = re.search(r'Correlation:\s*(\w+)', str(data.get('correlation_log', '')))
                moon_nak = nak_match.group(1) if nak_match else ''
            else:
                moon_sign = ''
                moon_nak = ''
            
            venus_data = vedic.get('Venus', vedic.get('VENUS', ''))
            if isinstance(venus_data, dict):
                venus_elong = venus_data.get('elongation_dir', '')
            elif isinstance(venus_data, str):
                # Check if Evening/Morning Star mentioned in astro context
                astro_str = str(data.get('astro_report', '')) + str(data.get('hora_forecast', ''))
                if 'Evening Star' in astro_str or 'sao tối' in astro_str.lower():
                    venus_elong = 'E'
                elif 'Morning Star' in astro_str or 'sao mai' in astro_str.lower():
                    venus_elong = 'W'
                else:
                    venus_elong = ''
            else:
                venus_elong = ''
            venus_phase = 'Evening Star' if venus_elong == 'E' else ('Morning Star' if venus_elong == 'W' else '')
            
            gann_held = data.get('gann_key_held', False)
            gann_status = 'held' if gann_held else ('breached' if data.get('gann_breached') else '')
            
            # Try multiple query strategies
            queries = []
            if moon_sign and moon_nak:
                queries.append(f"Moon in {moon_sign} Nakshatra {moon_nak}")
            if venus_phase:
                queries.append(f"Venus {venus_phase}")
            if gann_status:
                queries.append(f"Gann {gann_status}")
            
            if queries:
                rag_context = get_rag_context(
                    moon_sign=moon_sign,
                    moon_nakshatra=moon_nak,
                    venus_phase=venus_phase,
                    gann_status=gann_status,
                )
                similar = rag_context.get('similar_days', [])
                print(f"   ✅ RAG: Found {len(similar)} similar historical days")
                for r in similar[:3]:
                    m = r['metadata']
                    d = '🟢' if m.get('bullish') else '🔴'
                    print(f"      {d} {m.get('date', '?')} | {m.get('moon_sign', '')}/{m.get('moon_nakshatra', '')} | {m.get('volatility', '')}")
            else:
                print("   ⚠️ No astro conditions available for RAG query")
        except Exception as e:
            print(f"   ⚠️ RAG search failed: {e}")
    else:
        print("   ⚠️ RAG not available — skipping historical patterns")

    # ── Step 2: Generate Format B+ report ──
    print()
    print("📝 Step 2/3 — Generating Format B+ report (10 sections)...")
    try:
        # Inject RAG context into data for ReportGenerator
        if rag_context and rag_context.get('similar_days'):
            data['rag_historical_context'] = format_for_llm(rag_context)
            data['rag_similar_days'] = rag_context['similar_days']
        content = ReportGenerator.generate_patreon_report(data)
    except Exception as e:
        print(f"❌ generate_patreon_report failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Verify content
    sections_found = content.count('## ') + content.count('##  ')
    print(f"   ✅ Generated {len(content):,} chars, ~{sections_found} sections detected")

    # ── Step 3: Save to disk ──
    print()
    print("💾 Step 3/3 — Saving files...")

    # 3a. Main content for patreon_poster.js
    main_path = Path(WORKSPACE) / "patreon-db" / "patreon-post-content-v3.md"
    with open(main_path, 'w') as f:
        f.write(content)
    print(f"   ✅ {main_path}")

    # 3b. Archive
    archive_path = OUTPUT_DIR / f"patreon_post_{date_str}.md"
    with open(archive_path, 'w') as f:
        f.write(content)
    print(f"   ✅ {archive_path}")

    # ── Summary ──
    print()
    print("─" * 50)
    print("📊 PATREON POST SUMMARY")
    print("─" * 50)
    print(f"Format:   B+ (10 sections — Executive Summary, Macro, Technical,")
    print(f"          Vedic Astrology, Historical Correlation, Aether AI Deep Analysis,")
    print(f"          Strategy, Risk Matrix, Forward Outlook, Super Cycle Countdown)")
    # Show actual AI model used (detect from carmen_analyst env or fallback)
    ai_label = 'Rule-based (fallback)'
    if carmen and not carmen.get('error'):
        backend = os.environ.get('CARMEN_BACKEND', 'gemini')
        model = os.environ.get('CARMEN_MODEL', 'deepseek-chat' if backend == 'deepseek' else 'gemini-2.5-flash')
        display_name = {'deepseek': 'DeepSeek', 'gemini': 'Gemini'}.get(backend, backend)
        ai_label = f'{display_name} ({model})'
    print(f"AI:       {ai_label}")
    print(f"Price:    ${price:.1f}")
    if carmen and not carmen.get('error'):
        print(f"Signal:   {carmen.get('bias', 'N/A')} | {carmen.get('confidence', 0)*100:.0f}%")
    print(f"Chars:    {len(content):,}")
    print(f"Sections: {sections_found}")
    print()
    print("📋 Next: patreon_poster.js → Patreon draft (by cron 00:35)")
    print("─" * 50)

    return True


if __name__ == '__main__':
    forecast = '--tomorrow' in sys.argv
    success = generate_patreon_content(forecast_tomorrow=forecast)
    sys.exit(0 if success else 1)
