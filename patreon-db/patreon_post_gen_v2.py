#!/usr/bin/env python3
"""
patreon_post_gen_v2.py — Carmen's Patreon Post Generator V2 (Format B)

Uses get_full_report_data() + ReportGenerator.generate_patreon_report() to
output the approved 9-section Format B with:
  - Carmen AI (Gemini) analysis
  - 4-year historical correlation
  - Macro context (DXY, Fed, news)
  - Multi-TF Technical
  - Risk Matrix (6 types)
  - Forward Outlook 3-7 days

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

TZ = pytz.timezone("Asia/Ho_Chi_Minh")
OUTPUT_DIR = Path(WORKSPACE) / "patreon-db" / "patreon_posts"
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_patreon_content(forecast_tomorrow=False):
    """
    Generate Format B Patreon report (9 sections).

    Args:
        forecast_tomorrow: If True, mention next trading day in output.
                           (Data is still latest available — no prediction)

    Returns:
        bool — True on success
    """
    now = datetime.now(TZ)
    date_str = now.strftime("%Y-%m-%d")

    print(f"🪐 Carmen — Patreon Content Generator V2 (Format B)")
    print(f"📅 {date_str} | {'🌤️ Forecast mode' if forecast_tomorrow else '📊 Current analysis'}")
    print()

    # ── Step 1: Get full report data ──
    print("📡 Step 1/3 — Fetching market data + Carmen AI...")
    try:
        data = get_full_report_data(include_carmen=True)
    except Exception as e:
        print(f"❌ get_full_report_data failed: {e}")
        print("   Retrying without Carmen AI (fallback)...")
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
        print(f"   ✅ Carmen AI — Bias: {ca.get('bias', 'N/A')} | Confidence: {ca.get('confidence', 0)*100:.0f}%")
    else:
        print(f"   ⚠️ Carmen AI unavailable — using rule-based fallback")
    print(f"   ✅ Price: ${price:.1f} | Gann base: {data.get('gann_base', 'N/A')}")
    print(f"   ✅ Vedic: {len(data.get('vedic_planets', {}))} planets | Hora: {data.get('hora', {}).get('hora', 'N/A')}")

    # ── Step 2: Generate Format B report ──
    print()
    print("📝 Step 2/3 — Generating Format B report (9 sections)...")
    try:
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
    print(f"Format:   B (9 sections — Executive Summary, Macro, Technical,")
    print(f"          Vedic Astrology, Historical Correlation, Carmen AI Deep Analysis,")
    print(f"          Strategy, Risk Matrix, Forward Outlook)")
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
