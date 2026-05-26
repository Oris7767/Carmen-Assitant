#!/usr/bin/env python3
"""
Astro-Quant Scoring Engine
Implements Layer 4 (Dynamic Scoring) of the Astro-Quant Framework.
Regime-aware scoring with ATR-based weight adjustment.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json

class AstroQuantScorer:
    """Quantitative scoring engine for Gold (XAUUSD) trading signals."""
    
    # ═══════════════════════════════════════════════
    # LAYER 4: DYNAMIC SCORING WEIGHTS
    # ═══════════════════════════════════════════════
    
    # BASE WEIGHTS — applied regardless of regime
    SCORE_BULLISH = 'bullish'
    SCORE_BEARISH = 'bearish'
    
    # STATIC WEIGHT TABLES (from backtest data, 1103 days)
    
    # ---- NAKSHATRA SCORES (Layer 2: Astro) ----
    # Weight: 3 pts max (strongest single predictor, spread 61-88%)
    NAKSHATRA_SCORES = {
        # Bullish cluster
        'Mula': +3.0,                # 73.2% bullish, strongest
        'Purva Ashadha': +3.0,       # 68.4% bullish
        'Ashwini': +2.0,             # 62.5% bullish
        'Chitra': +1.0,              # 57.9%
        'Vishakha': +1.0,            # 57.9%
        'Ashlesha': +0.5,            # 56.8%
        'Uttara Phalguni': +0.5,     # 56.8%
        'Punarvasu': +0.5,           # 55.0%
        'Rohini': +0.5,              # 54.8%
        'Magha': +0.5,               # 53.5%
        # Neutral
        'Shravana': 0.0,             # 52.8%
        'Revati': 0.0,               # 52.5%
        'Shatabhisha': 0.0,          # 52.5%
        'Swati': 0.0,                # 52.4%
        'Hasta': 0.0,                # 52.3%
        'Ardra': -0.5,               # 51.2%
        'Bharani': 0.0,              # 50.0%
        'Purva Phalguni': -0.5,      # 47.7%
        'Jyeshtha': -1.0,            # 46.2%
        'Krittika': -1.0,            # 46.2%
        'Uttara Ashadha': -1.0,      # 46.2%
        # Bearish cluster
        'Pushya': -1.5,              # 42.6%
        'Purva Bhadrapada': -2.0,    # 40.0%
        'Mrigashira': -2.0,          # 39.5%
        'Dhanishta': -2.0,           # 38.5%
        'Anuradha': -2.0,            # 38.3%
        'Uttara Bhadrapada': -3.0,   # 37.1% — weakest
    }
    
    # ---- MOON SIGN SCORES ----
    # Weight: 2 pts max
    MOON_SIGN_SCORES = {
        'Sagittarius': +2.0,   # 71.6% — strongest, consistent across all periods
        'Libra': +1.0,         # 57.1%
        'Leo': +1.0,           # 54.1%
        'Aries': +0.5,         # 53.5%
        'Virgo': 0.0,          # 51.6%
        'Cancer': 0.0,         # 51.5%
        'Taurus': 0.0,         # 50.0%
        'Gemini': -0.5,        # 48.4%
        'Pisces': -0.5,        # 45.9%
        'Capricorn': -1.0,     # 44.2%
        'Aquarius': -1.0,      # 43.8%
        'Scorpio': -2.0,       # 42.1% — weakest
    }
    
    # ---- PLANET RETROGRADE SCORES ----
    RETRO_SCORES = {
        'mars_retro': +2.0,       # 60.2% bullish, +10% delta — consistent
        'mercury_retro': +1.0,    # 53.6%, +3% delta
        'venus_retro': +0.5,      # 51.9%, +0.8% delta
        'jupiter_retro': -0.5,    # 49.4%, -2.5% delta
        'saturn_retro': -1.0,     # 47.9%, -4.9% delta
    }
    
    # ---- COMBUST SCORES ----
    COMBUST_SCORES = {
        'mercury_combust': +3.0,  # 66.1% bullish, +0.38% — massive signal
        'venus_combust': -0.5,    # 49.3% bullish
        'mars_combust': +0.0,     # 47.6% (BUT range $64.3 → high vol penalty)
    }
    
    # ---- HORA SCORES ----
    HORA_SCORES = {
        'Venus': +1.0,      # 52.7% bullish
        'Jupiter': +0.5,    # 52.5%
        'Moon': 0.0,        # 51.0%
        'Mercury': -0.5,    # 50.0%
        'Mars': -1.0,       # 49.6%
        'Sun': 0.0,
        'Saturn': -0.5,
    }
    
    # ---- MOON PHASE SCORES ----
    MOON_PHASE_SCORES = {
        'First Quarter': +1.0,       # 57.6% — strongest bullish
        'Waxing Gibbous': +0.5,      # 53.4%
        'Waning Gibbous': 0.0,       # 51.9%
        'Waning Crescent': 0.0,      # 50.7%
        'New Moon': 0.0,             # 50.0%
        'Last Quarter': 0.0,         # 49.6%
        'Full Moon': -0.5,           # 48.9%
        'Waxing Crescent': -1.0,     # 46.8% — weakest
    }
    
    # ---- ASPECT SCORES (from 1103-day backtest) ----
    ASPECT_SCORES = {
        # Strong bullish aspects
        'Sun Opposition Mars': +3.0,           # 80.0% bullish
        'Jupiter Sextile Ketu': +3.0,          # 80.0%
        'Jupiter Trine Rahu': +3.0,            # 80.0%
        'Sun Conjunction Ketu': +2.5,          # 70.4%
        'Sun Opposition Rahu': +2.5,           # 70.4%
        'Mercury Conjunction Ketu': +2.5,      # 71.4%
        'Mercury Opposition Rahu': +2.5,       # 71.4%
        'Sun Conjunction Saturn': +2.0,         # 69.2%
        'Sun Square Saturn': +2.0,             # 68.9%
        'Moon Sextile Jupiter': +2.0,          # 68.2%
        'Venus Trine Ketu': +1.5,              # 65.9%
        'Venus Sextile Rahu': +1.5,            # 65.9%
        'Sun Square Moon': +1.5,               # 64.7%
        'Moon Square Mars': +1.5,              # 64.4%
        'Venus Square Saturn': +1.5,           # 63.9%
        'Mercury Square Ketu': +1.5,           # 63.6%
        'Mars Sextile Jupiter': +1.5,          # 63.6%
        'Moon Square Rahu': +1.5,              # 63.0%
        'Moon Square Ketu': +1.5,              # 63.0%
        'Sun Trine Moon': +1.5,                # 62.5%
        'Moon Conjunction Ketu': +1.5,         # 62.5%
        'Moon Opposition Rahu': +1.5,          # 62.5%
        'Mars Square Saturn': +1.5,            # 62.5%
        'Mercury Trine Saturn': +1.5,          # 62.2%
        'Moon Opposition Sun': +1.0,           # 60.0%
        'Sun Conjunction Jupiter': +0.5,       # 56.8%
        'Sun Conjunction Mercury': +0.5,       # 55.1%
        'Sun Conjunction Moon': +0.5,          # 53.8%
        'Sun Opposition Jupiter': +0.5,        # 53.8%
        'Sun Sextile Jupiter': +0.5,           # 53.6%
        'Sun Conjunction Venus': +0.5,         # 51.6%
        'Sun Sextile Moon': 0.0,               # 50.9%
        # Bearish aspects
        'Mars Conjunction Rahu': -2.0,         # 37.9% (with Ketu opp)
        'Mars Opposition Ketu': -2.0,          # 37.9%
        'Jupiter Opposition Ketu': -2.0,       # 38.5%
        'Jupiter Conjunction Rahu': -2.0,      # 38.5%
        'Mercury Conjunction Jupiter': -2.0,   # 38.9%
        'Venus Square Jupiter': -2.0,          # 39.1%
        'Mercury Conjunction Mars': -2.0,      # 39.5%
        'Sun Trine Jupiter': -2.0,             # 40.0%
        'Moon Trine Jupiter': -1.5,            # 42.9%
        'Saturn Sextile Rahu': -1.5,           # 42.9%
        'Saturn Trine Ketu': -1.5,             # 42.9%
        'Venus Conjunction Jupiter': -1.5,     # 42.9%
        'Moon Conjunction Mercury': -1.5,      # 42.9%
        'Mars Trine Jupiter': -1.5,            # 43.2%
        'Sun Opposition Saturn': -1.5,         # 43.3%
        'Saturn Opposition Ketu': -1.5,        # 45.5%
        'Saturn Conjunction Rahu': -1.5,       # 45.5%
        'Mercury Trine Mars': -2.0,            # 35.3% — most bearish aspect
    }
    
    # ---- GANN SCORES ----
    GANN_HELD_SCORE = +1.0            # 51.3% bullish, range 23.1
    GANN_BREACHED_SCORE = 0.0         # 49.6% bullish, BUT range 92.4 (4x) → vol penalty
    
    # ---- EMA SCORES ----
    EMA_ABOVE_SCORE = +1.0            # EMA31 > EMA113: 52.9% bullish
    EMA_BELOW_SCORE = -1.0            # EMA31 < EMA113: 43.1% bullish
    
    # ---- MACRO SCORES ----
    DXY_BULLISH_SCORE = -1.5          # Inverse: 36.8% gold bullish
    DXY_BEARISH_SCORE = +1.5          # 65.0% gold bullish
    US10Y_RISING_SCORE = -1.5         # 42.1% gold bullish
    US10Y_FALLING_SCORE = +1.5        # 59.6% gold bullish
    
    # ---- VENUS/MERCURY PHASE SCORES (from Deep Analysis) ----
    VENUS_MORNING_STAR_SCORE = 0.0    # 51.2% — neutral
    VENUS_EVENING_STAR_SCORE = 0.0    # 51.1% — neutral
    MERCURY_MORNING_STAR_SCORE = 0.0  # 50.6%
    MERCURY_EVENING_STAR_SCORE = 0.0  # 51.7%
    
    # ---- EVENT SCORES ----
    EVENT_HIGH_IMPACT_PENALTY = -0.5  # Slightly bearish on high impact days
    FOMC_NEUTRAL = 0.0               # 50% at FOMC
    NFP_SCORE = -0.5                  # NFP days: slightly bearish
    CPI_SCORE = -0.5                  # CPI: 47.8% bullish
    ISM_MFG_SCORE = +1.0             # ISM Manufacturing: 69.2% bullish
    
    # ═══════════════════════════════════════════════
    # VOLATILITY REGIME DETECTION
    # ═══════════════════════════════════════════════
    
    @staticmethod
    def detect_volatility_regime(gold_range, volatility_label=None):
        """
        Detect volatility regime from range or label.
        Returns: 'low', 'medium', or 'high'
        """
        if volatility_label:
            return volatility_label
        if gold_range is None:
            return 'medium'
        if gold_range < 15:
            return 'low'
        if gold_range > 50:
            return 'high'
        return 'medium'
    
    # ═══════════════════════════════════════════════
    # REGIME-AWARE WEIGHT ADJUSTMENT
    # ═══════════════════════════════════════════════
    
    @staticmethod
    def get_regime_weights(volatility_regime):
        """
        Returns weight multipliers per signal category based on volatility regime.
        
        Logic:
        - LOW volatility: Technical (Gann) weights increase, astro aspects decrease
        - HIGH volatility: Aspects + Gann weights dominate, Hora/minor signals fade
        - MEDIUM: Balanced default weights
        """
        if volatility_regime == 'low':
            return {
                'nakshatra': 1.0,
                'moon_sign': 1.0,
                'retro': 1.0,
                'combust': 0.8,
                'hora': 0.5,        # Hora less relevant in low vol
                'moon_phase': 1.0,
                'aspects': 0.7,      # Aspects matter less in low vol
                'gann': 1.5,         # Gann MORE relevant in low vol
                'ema': 1.5,          # Trend following matters more
                'dxy': 1.2,
                'us10y': 1.2,
                'venus_phase': 0.5,
                'mercury_phase': 0.5,
            }
        elif volatility_regime == 'high':
            return {
                'nakshatra': 1.3,
                'moon_sign': 1.0,
                'retro': 1.2,
                'combust': 1.5,      # Combust effects amplify in high vol
                'hora': 0.3,         # Hora nearly irrelevant in high vol
                'moon_phase': 0.8,
                'aspects': 1.5,      # Aspects DOMINATE in high vol
                'gann': 2.0,         # Gann breach = critical in high vol
                'ema': 0.5,          # Trend less reliable in high vol chop
                'dxy': 0.8,
                'us10y': 0.8,
                'venus_phase': 0.8,
                'mercury_phase': 0.8,
            }
        else:  # medium
            return {
                'nakshatra': 1.0,
                'moon_sign': 1.0,
                'retro': 1.0,
                'combust': 1.0,
                'hora': 1.0,
                'moon_phase': 1.0,
                'aspects': 1.0,
                'gann': 1.0,
                'ema': 1.0,
                'dxy': 1.0,
                'us10y': 1.0,
                'venus_phase': 1.0,
                'mercury_phase': 1.0,
            }
    
    # ═══════════════════════════════════════════════
    # MAIN SCORING FUNCTION
    # ═══════════════════════════════════════════════
    
    @classmethod
    def score(cls, row, volatility_regime=None):
        """
        Main scoring function.
        Input: A single row (dict or pandas Series) with astro/macro/technical data.
        Output: {
            'composite_score': float (-10 to +10),
            'signal': 'LONG' | 'SHORT' | 'NEUTRAL',
            'confidence': 'HIGH' | 'MEDIUM' | 'LOW',
            'market_state': 'expansion' | 'compression' | 'exhaustion' | 'fear',
            'details': {...}
        }
        """
        # Determine volatility regime
        gold_range = row.get('gold_range')
        vol_label = row.get('volatility')
        regime = cls.detect_volatility_regime(gold_range, vol_label)
        if volatility_regime:
            regime = volatility_regime
        
        weights = cls.get_regime_weights(regime)
        
        score = 0.0
        details = {}
        max_possible = 0.0
        
        # 1. Nakshatra (max ±3.0)
        nakshatra = row.get('moon_nakshatra')
        if nakshatra and nakshatra in cls.NAKSHATRA_SCORES:
            ns = cls.NAKSHATRA_SCORES[nakshatra]
            score += ns * weights['nakshatra']
            max_possible += 3.0 * weights['nakshatra']
            details['nakshatra'] = {'value': nakshatra, 'score': ns, 'weighted': ns * weights['nakshatra']}
        
        # 2. Moon Sign (max ±2.0)
        moon_sign = row.get('moon_sign')
        if moon_sign and moon_sign in cls.MOON_SIGN_SCORES:
            ms = cls.MOON_SIGN_SCORES[moon_sign]
            score += ms * weights['moon_sign']
            max_possible += 2.0 * weights['moon_sign']
            details['moon_sign'] = {'value': moon_sign, 'score': ms, 'weighted': ms * weights['moon_sign']}
        
        # 3. Retrogrades
        retro_total = 0.0
        for planet, retro_score in cls.RETRO_SCORES.items():
            if row.get(planet, False):
                retro_total += retro_score * weights['retro']
        score += retro_total
        max_possible += 3.0 * weights['retro']
        details['retro'] = {'total': retro_total, 'weighted': retro_total}
        
        # 4. Combust
        combust_total = 0.0
        for planet, comb_score in cls.COMBUST_SCORES.items():
            if row.get(planet, False):
                combust_total += comb_score * weights['combust']
        score += combust_total
        max_possible += 3.0 * weights['combust']
        details['combust'] = {'total': combust_total, 'weighted': combust_total}
        
        # 5. Hora
        hora = row.get('dominant_planet_hour')
        if hora and hora in cls.HORA_SCORES:
            hs = cls.HORA_SCORES[hora] * weights['hora']
            score += hs
            max_possible += 1.0 * weights['hora']
            details['hora'] = {'value': hora, 'score': hs}
        
        # 6. Moon Phase
        moon_phase = row.get('moon_phase')
        if moon_phase and moon_phase in cls.MOON_PHASE_SCORES:
            mp = cls.MOON_PHASE_SCORES[moon_phase] * weights['moon_phase']
            score += mp
            max_possible += 1.0 * weights['moon_phase']
            details['moon_phase'] = {'value': moon_phase, 'score': mp}
        
        # 7. Aspects (parse from aspects_json)
        aspects_total = 0.0
        aspects_detail = []
        aspects_json = row.get('aspects_json')
        if aspects_json and not pd.isna(aspects_json) and str(aspects_json).strip() not in ['', 'nan']:
            try:
                aspects = json.loads(str(aspects_json)) if isinstance(aspects_json, str) else aspects_json
                for asp in aspects:
                    p1 = asp.get('planet1', '')
                    p2 = asp.get('planet2', '')
                    asp_type = asp.get('aspect', '')
                    key = f"{p1} {asp_type} {p2}"
                    if key in cls.ASPECT_SCORES:
                        as_ = cls.ASPECT_SCORES[key] * weights['aspects']
                        aspects_total += as_
                        aspects_detail.append({'aspect': key, 'score': as_})
            except:
                pass
        score += aspects_total
        max_possible += 6.0 * weights['aspects']
        details['aspects'] = {'total': aspects_total, 'details': aspects_detail}
        
        # 8. Gann Key Level (use gann_held for structural S/R, fallback to gann_key_level_held)
        gann_held_val = row.get('gann_held')
        if gann_held_val is None:
            gann_held_val = row.get('gann_key_level_held')
        if gann_held_val is not None:
            gs = (cls.GANN_HELD_SCORE if gann_held_val else cls.GANN_BREACHED_SCORE) * weights['gann']
            score += gs
            max_possible += 1.0 * weights['gann']
            details['gann'] = {'held': bool(gann_held_val), 'score': round(gs, 2)}
            
            # HIGH VOL risk flag for breached
            if not gann_held_val:
                details['high_vol_alert'] = 'GANN BREACHED — expect 4x range'
        
        # 9. EMA
        ema = row.get('gold_ema_relation')
        if ema:
            es = (cls.EMA_ABOVE_SCORE if ema == 'above' else cls.EMA_BELOW_SCORE) * weights['ema']
            score += es
            max_possible += 1.0 * weights['ema']
            details['ema'] = {'relation': ema, 'score': es}
        
        # 10. DXY
        dxy_dir = row.get('dxy_direction')
        if dxy_dir:
            if dxy_dir == 'bullish':
                ds = cls.DXY_BULLISH_SCORE * weights['dxy']
            elif dxy_dir == 'bearish':
                ds = cls.DXY_BEARISH_SCORE * weights['dxy']
            else:
                ds = 0.0
            score += ds
            max_possible += 1.5 * weights['dxy']
            details['dxy'] = {'direction': dxy_dir, 'score': ds}
        
        # 11. US10Y
        us10y_chg = row.get('us10y_change')
        if us10y_chg is not None and not pd.isna(us10y_chg):
            if us10y_chg > 0.01:
                us = cls.US10Y_RISING_SCORE * weights['us10y']
            elif us10y_chg < -0.01:
                us = cls.US10Y_FALLING_SCORE * weights['us10y']
            else:
                us = 0.0
            score += us
            max_possible += 1.5 * weights['us10y']
            details['us10y'] = {'change': us10y_chg, 'score': us}
        
        # 12. Venus Phase
        venus_dir = row.get('venus_elong_dir')
        if venus_dir:
            vs = (cls.VENUS_MORNING_STAR_SCORE if venus_dir == 'W' else cls.VENUS_EVENING_STAR_SCORE)
            vs *= weights['venus_phase']
            score += vs
            details['venus_phase'] = {'dir': venus_dir, 'score': vs}
        
        # 13. Mercury Phase  
        merc_dir = row.get('mercury_elong_dir')
        if merc_dir:
            ms = (cls.MERCURY_MORNING_STAR_SCORE if merc_dir == 'W' else cls.MERCURY_EVENING_STAR_SCORE)
            ms *= weights['mercury_phase']
            score += ms
            details['mercury_phase'] = {'dir': merc_dir, 'score': ms}
        
        # 14. Mars Combust HIGH VOL penalty
        if row.get('mars_combust', False):
            details['mars_combust_alert'] = 'MARS COMBUST — avg range $64.3, high vol'
        
        # 15. Economic events
        impact = row.get('economic_impact')
        if impact == 'high':
            score += cls.EVENT_HIGH_IMPACT_PENALTY * weights['gann']
            details['eco_impact'] = 'HIGH impact economic event'
        
        # ═══════════════════════════════════════════════
        # NORMALIZE & CLASSIFY
        # ═══════════════════════════════════════════════
        
        # Normalize to -10 to +10 scale
        if max_possible > 0:
            normalized = (score / max_possible) * 10
        else:
            normalized = 0.0
        
        # Clamp
        normalized = max(-10.0, min(10.0, normalized))
        
        # Signal
        if normalized >= 3.0:
            signal = 'LONG'
            confidence = 'HIGH' if normalized >= 6.0 else 'MEDIUM'
        elif normalized <= -3.0:
            signal = 'SHORT'
            confidence = 'HIGH' if normalized <= -6.0 else 'MEDIUM'
        else:
            signal = 'NEUTRAL'
            confidence = 'LOW'
        
        # Market State (Layer 3)
        if normalized >= 4.0 and regime != 'high':
            market_state = 'expansion'
        elif normalized <= -4.0 and regime != 'high':
            market_state = 'expansion'  # strong trend, direction doesn't matter for phase
        elif regime == 'low' and abs(normalized) < 3.0:
            market_state = 'compression'
        elif regime == 'high':
            market_state = 'fear'
        elif abs(normalized) < 2.0:
            market_state = 'exhaustion'
        else:
            market_state = 'expansion'
        
        return {
            'composite_score': round(normalized, 1),
            'signal': signal,
            'confidence': confidence,
            'market_state': market_state,
            'volatility_regime': regime,
            'raw_score': round(score, 2),
            'max_possible': round(max_possible, 2),
            'details': details
        }
    
    # ═══════════════════════════════════════════════
    # BATCH BACKTEST
    # ═══════════════════════════════════════════════
    
    @classmethod
    def backtest(cls, df):
        """Run full scoring on historical data and compute win-rate."""
        results = []
        for _, row in df.iterrows():
            try:
                result = cls.score(row)
                result['date'] = row.get('date')
                result['actual_bullish'] = row.get('gold_bullish')
                result['actual_change'] = row.get('gold_change_pct')
                result['actual_range'] = row.get('gold_range')
                results.append(result)
            except Exception as e:
                print(f"Error scoring row: {e}")
                continue
        
        results_df = pd.DataFrame(results)
        
        # Win rate analysis
        if 'actual_bullish' in results_df.columns:
            long_signals = results_df[results_df['signal'] == 'LONG']
            short_signals = results_df[results_df['signal'] == 'SHORT']
            
            long_wins = (long_signals['actual_bullish'] == True).sum() if len(long_signals) > 0 else 0
            short_wins = (short_signals['actual_bullish'] == False).sum() if len(short_signals) > 0 else 0
            
            stats = {
                'total_days': len(results_df),
                'long_signals': len(long_signals),
                'short_signals': len(short_signals),
                'neutral_signals': len(results_df[results_df['signal'] == 'NEUTRAL']),
                'long_win_rate': round(long_wins / len(long_signals) * 100, 1) if len(long_signals) > 0 else 0,
                'short_win_rate': round(short_wins / len(short_signals) * 100, 1) if len(short_signals) > 0 else 0,
                'long_avg_change': round(long_signals['actual_change'].mean(), 3) if len(long_signals) > 0 else 0,
                'short_avg_change': round(short_signals['actual_change'].mean(), 3) if len(short_signals) > 0 else 0,
                'high_conf_long_win_rate': None,
                'high_conf_short_win_rate': None,
            }
            
            # High confidence stats
            hc_long = long_signals[long_signals['confidence'] == 'HIGH']
            hc_short = short_signals[short_signals['confidence'] == 'HIGH']
            if len(hc_long) > 0:
                stats['high_conf_long_win_rate'] = round(hc_long['actual_bullish'].sum() / len(hc_long) * 100, 1)
                stats['high_conf_long_count'] = len(hc_long)
            if len(hc_short) > 0:
                stats['high_conf_short_win_rate'] = round((~hc_short['actual_bullish']).sum() / len(hc_short) * 100, 1)
                stats['high_conf_short_count'] = len(hc_short)
            
            return results_df, stats
        
        return results_df, {}


# ═══════════════════════════════════════════════
# RUN BACKTEST ON FULL DATASET
# ═══════════════════════════════════════════════
if __name__ == '__main__':
    DATA_DIR = Path("/Users/kimssa/.openclaw/workspace/patreon-db/data")
    
    print("Loading data for backtest...")
    dfs = []
    for f in sorted(DATA_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"Error: {f}: {e}")
    full_df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(full_df)} rows")
    
    print("\nRunning Astro-Quant Scorer backtest...")
    results_df, stats = AstroQuantScorer.backtest(full_df)
    
    print("\n" + "="*60)
    print("ASTRO-QUANT SCORER — BACKTEST RESULTS")
    print("="*60)
    print(f"Total days scored: {stats['total_days']}")
    print(f"LONG signals:  {stats['long_signals']}  → Win rate: {stats['long_win_rate']}%  → AvgΔ: {stats['long_avg_change']:+.3f}%")
    print(f"SHORT signals: {stats['short_signals']}  → Win rate: {stats['short_win_rate']}%  → AvgΔ: {stats['short_avg_change']:+.3f}%")
    print(f"NEUTRAL:       {stats['neutral_signals']}")
    
    if stats.get('high_conf_long_win_rate'):
        print(f"\nHIGH CONF LONG:  {stats['high_conf_long_count']} signals, Win rate: {stats['high_conf_long_win_rate']}%")
    if stats.get('high_conf_short_win_rate'):
        print(f"HIGH CONF SHORT: {stats['high_conf_short_count']} signals, Win rate: {stats['high_conf_short_win_rate']}%")
    
    # Market state distribution
    if 'market_state' in results_df.columns:
        print(f"\nMarket State Distribution:")
        for state in ['expansion', 'compression', 'exhaustion', 'fear']:
            cnt = len(results_df[results_df['market_state'] == state])
            print(f"  {state}: {cnt} days ({cnt/len(results_df)*100:.1f}%)")
    
    # Volatility regime distribution
    if 'volatility_regime' in results_df.columns:
        print(f"\nVolatility Regime Distribution:")
        for reg in ['low', 'medium', 'high']:
            cnt = len(results_df[results_df['volatility_regime'] == reg])
            print(f"  {reg}: {cnt} days ({cnt/len(results_df)*100:.1f}%)")
            
    print("\n✅ Backtest complete.")
