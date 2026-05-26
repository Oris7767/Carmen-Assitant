"""
historical_correlation.py — Query 4 years of patreon-db data to find
historically similar days and compute correlation statistics.

Used by report_generator.py for Patreon premium posts.

Usage:
    from historical_correlation import HistoricalCorrelation
    hc = HistoricalCorrelation()
    stats = hc.correlate(moon_nakshatra='Magha', moon_sign='Leo', ...)
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter

DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "patreon-db" / "data"

# ── Nakshatra quality labels (for narrative) ──
NAKSHATRA_QUALITIES = {
    'Ashwini': 'Nhanh, đột phá, năng lượng mới',
    'Bharani': 'Chịu đựng, kiềm chế, tích lũy',
    'Krittika': 'Sắc bén, cắt giảm, thanh lọc',
    'Rohini': 'Tăng trưởng, vật chất, hưởng thụ',
    'Mrigashira': 'Tìm kiếm, do dự, phân nhánh',
    'Ardra': 'Hủy diệt, biến động, đổi mới',
    'Punarvasu': 'Phục hồi, quay lại, tái sinh',
    'Pushya': 'Nuôi dưỡng, ổn định, bảo thủ',
    'Ashlesha': 'Thao túng, đầu cơ, bẫy giá',
    'Magha': 'Quyền lực, lãnh đạo, đỉnh cao',
    'Purva Phalguni': 'Sáng tạo, hưởng thụ, nghỉ ngơi',
    'Uttara Phalguni': 'Cam kết, hợp đồng, ổn định',
    'Hasta': 'Khéo léo, chính xác, thủ công',
    'Chitra': 'Xây dựng, kiến trúc, cơ hội',
    'Swati': 'Độc lập, tự do, phân tán',
    'Vishakha': 'Mục tiêu kép, quyết đoán, đột phá',
    'Anuradha': 'Kiên nhẫn, tích lũy ngầm, chiến lược',
    'Jyeshtha': 'Cạnh tranh, quyền lực ngầm, rủi ro',
    'Mula': 'Đào sâu, phá hủy gốc rễ, tái cấu trúc',
    'Purva Ashadha': 'Chiến thắng, mở rộng, tuyên bố',
    'Uttara Ashadha': 'Chiến thắng cuối cùng, bền vững',
    'Shravana': 'Lắng nghe, học hỏi, kết nối',
    'Dhanishta': 'Giàu có, âm nhạc, nhịp điệu',
    'Shatabhisha': 'Trị liệu, ẩn giấu, bí ẩn',
    'Purva Bhadrapada': 'Tâm linh, hy sinh, biến đổi',
    'Uttara Bhadrapada': 'Từ bỏ, giải thoát, kết thúc',
    'Revati': 'Hoàn thành, khép lại, chuyển giao',
}


class HistoricalCorrelation:
    """
    Query engine for historical pattern matching across 4+ years of data.
    """

    def __init__(self):
        self._df = None

    @property
    def df(self):
        """Lazy-load and cache the full dataset."""
        if self._df is None:
            dfs = []
            for f in sorted(DATA_DIR.glob("*.csv")):
                try:
                    dfs.append(pd.read_csv(f))
                except Exception:
                    pass
            if dfs:
                self._df = pd.concat(dfs, ignore_index=True)
            else:
                self._df = pd.DataFrame()
        return self._df

    # ──────────────────────────────────────────────
    # MAIN: correlate today's setup against history
    # ──────────────────────────────────────────────

    def correlate(self, moon_nakshatra=None, moon_sign=None,
                  moon_phase=None, sun_sign=None,
                  planet_aspects=None, dominant_hora=None,
                  volatility=None, trend=None,
                  gann_held=None, market_reaction=None,
                  merc_elong=None, venus_elong=None,
                  mars_retro=None, venus_retro=None,
                  saturn_retro=None, jupiter_retro=None):
        """
        Find historically similar days and return correlation stats.
        
        Returns dict with:
          - nakshatra_stats, moon_sign_stats, moon_phase_stats
          - aspect_stats
          - exact_matches (top 5 most similar days)
          - composite: overall historical baseline
        """
        df = self.df
        if df.empty:
            return {'error': 'No historical data loaded'}

        result = {}

        # ── 1. Nakshatra Performance ──
        if moon_nakshatra:
            nak_df = df[df['moon_nakshatra'] == moon_nakshatra]
            n = len(nak_df)
            if n > 0:
                bull = nak_df['gold_bullish'].sum()
                avg_chg = nak_df['gold_change_pct'].mean()
                avg_range = nak_df['gold_range'].mean()
                reactions = Counter(nak_df['market_reaction'].dropna())
                best_r = reactions.most_common(2)
                vols = Counter(nak_df['volatility'].dropna())
                dom_vol = vols.most_common(1)[0][0] if vols else 'unknown'

                result['nakshatra_stats'] = {
                    'nakshatra': moon_nakshatra,
                    'quality': NAKSHATRA_QUALITIES.get(moon_nakshatra, ''),
                    'total_days': n,
                    'bullish_pct': round(bull / n * 100, 1),
                    'avg_change_pct': round(avg_chg, 3),
                    'avg_range': round(avg_range, 1),
                    'dominant_volatility': dom_vol,
                    'dominant_reaction': best_r,
                }

        # ── 2. Moon Sign Performance ──
        if moon_sign:
            ms_df = df[df['moon_sign'] == moon_sign]
            n = len(ms_df)
            if n > 0:
                bull = ms_df['gold_bullish'].sum()
                avg_chg = ms_df['gold_change_pct'].mean()
                avg_range = ms_df['gold_range'].mean()

                result['moon_sign_stats'] = {
                    'sign': moon_sign,
                    'total_days': n,
                    'bullish_pct': round(bull / n * 100, 1),
                    'avg_change_pct': round(avg_chg, 3),
                    'avg_range': round(avg_range, 1),
                }

        # ── 3. Combined Nakshatra + Moon Sign ──
        if moon_nakshatra and moon_sign:
            combo = df[(df['moon_nakshatra'] == moon_nakshatra) &
                        (df['moon_sign'] == moon_sign)]
            n = len(combo)
            if n > 0:
                bull = combo['gold_bullish'].sum()
                avg_chg = combo['gold_change_pct'].mean()
                result['combined_stats'] = {
                    'total_days': n,
                    'bullish_pct': round(bull / n * 100, 1),
                    'avg_change_pct': round(avg_chg, 3),
                }

        # ── 4. Moon Phase ──
        if moon_phase:
            phase_df = df[df['moon_phase'] == moon_phase]
            n = len(phase_df)
            if n > 0:
                bull = phase_df['gold_bullish'].sum()
                avg_chg = phase_df['gold_change_pct'].mean()
                result['moon_phase_stats'] = {
                    'phase': moon_phase,
                    'total_days': n,
                    'bullish_pct': round(bull / n * 100, 1),
                    'avg_change_pct': round(avg_chg, 3),
                }

        # ── 5. Hora Performance ──
        if dominant_hora:
            hora_col = 'dominant_planet_hour'
            if hora_col in df.columns:
                hora_df = df[df[hora_col] == dominant_hora]
                n = len(hora_df)
                if n > 0:
                    bull = hora_df['gold_bullish'].sum()
                    avg_chg = hora_df['gold_change_pct'].mean()
                    result['dominant_hora_stats'] = {
                        'hora': dominant_hora,
                        'total_days': n,
                        'bullish_pct': round(bull / n * 100, 1),
                        'avg_change_pct': round(avg_chg, 3),
                    }

        # ── 6. Retrograde Effects ──
        retro_stats = {}
        for planet, col in [('Mars', 'mars_retro'), ('Venus', 'venus_retro'),
                             ('Saturn', 'saturn_retro'), ('Jupiter', 'jupiter_retro')]:
            if col in df.columns:
                retro_days = df[df[col] == True]
                direct_days = df[df[col] == False]
                if len(retro_days) > 10 and len(direct_days) > 10:
                    r_bull = retro_days['gold_bullish'].mean() * 100
                    d_bull = direct_days['gold_bullish'].mean() * 100
                    r_chg = retro_days['gold_change_pct'].mean()
                    d_chg = direct_days['gold_change_pct'].mean()
                    r_range = retro_days['gold_range'].mean()
                    d_range = direct_days['gold_range'].mean()
                    retro_stats[planet] = {
                        'retro_bullish': round(r_bull, 1),
                        'direct_bullish': round(d_bull, 1),
                        'retro_avg_change': round(r_chg, 3),
                        'direct_avg_change': round(d_chg, 3),
                        'retro_avg_range': round(r_range, 1),
                        'direct_avg_range': round(d_range, 1),
                        'delta_bullish': round(r_bull - d_bull, 1),
                    }
        if retro_stats:
            result['retro_stats'] = retro_stats

        # ── 7. Gann Key Level Held vs Breached ──
        if 'gann_key_level_held' in df.columns:
            held = df[df['gann_key_level_held'] == True]
            breached = df[df['gann_key_level_held'] == False]
            if len(held) > 10 and len(breached) > 10:
                result['gann_key_stats'] = {
                    'held_bullish_pct': round(held['gold_bullish'].mean() * 100, 1),
                    'breached_bullish_pct': round(breached['gold_bullish'].mean() * 100, 1),
                    'held_avg_range': round(held['gold_range'].mean(), 1),
                    'breached_avg_range': round(breached['gold_range'].mean(), 1),
                    'held_total': len(held),
                    'breached_total': len(breached),
                }

        # ── 8. Find Top 5 Exact Matches ──
        exact_matches = []
        if moon_nakshatra and moon_sign:
            candidates = df[(df['moon_nakshatra'] == moon_nakshatra) &
                             (df['moon_sign'] == moon_sign)]
            
            for _, row in candidates.iterrows():
                score = 0
                # Score by volatility match
                if volatility and row.get('volatility') == volatility:
                    score += 3
                # Score by trend match
                if trend and row.get('trend_direction') == trend:
                    score += 2
                # Score by gann held
                if gann_held is not None:
                    if row.get('gann_key_level_held') == gann_held:
                        score += 2
                # Score by market reaction
                if market_reaction and row.get('market_reaction') == market_reaction:
                    score += 1

                if score > 0:
                    exact_matches.append({
                        'date': str(row['date']),
                        'close': float(row['gold_close']),
                        'change_pct': float(row['gold_change_pct']),
                        'bullish': bool(row['gold_bullish']),
                        'range': float(row['gold_range']),
                        'volatility': str(row.get('volatility', '')),
                        'reaction': str(row.get('market_reaction', '')),
                        'moon_nakshatra': str(row.get('moon_nakshatra', '')),
                        'moon_sign': str(row.get('moon_sign', '')),
                        'dominant_hora': str(row.get('dominant_planet_hour', '')),
                        'similarity_score': score,
                    })

            exact_matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            result['exact_matches'] = exact_matches[:5]

        # ── 9. Overall Baseline ──
        total = len(df)
        if total > 0:
            bull_pct = df['gold_bullish'].sum() / total * 100
            avg_chg = df['gold_change_pct'].mean()
            avg_range = df['gold_range'].mean()
            result['baseline'] = {
                'total_days': total,
                'overall_bullish_pct': round(bull_pct, 1),
                'overall_avg_change': round(avg_chg, 3),
                'overall_avg_range': round(avg_range, 1),
                'date_range': f"{df['date'].min()} → {df['date'].max()}",
            }

        return result


# ── CLI for testing ──
if __name__ == "__main__":
    import sys
    hc = HistoricalCorrelation()
    print(f"Loaded {len(hc.df)} trading days")
    print(f"Range: {hc.df['date'].min()} → {hc.df['date'].max()}")
    print()

    # Test with today's setup
    stats = hc.correlate(
        moon_nakshatra='Magha',
        moon_sign='Leo',
        moon_phase='First Quarter',
        dominant_hora='Moon',
    )
    print(json.dumps(stats, indent=2, ensure_ascii=False, default=str))
