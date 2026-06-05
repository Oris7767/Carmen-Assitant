#!/usr/bin/env python3
"""
Astro-Quant Scoring Engine V3
Implements Layer 4 (Dynamic Scoring) of the Astro-Quant Framework V3.
Regime-aware scoring with ATR-based weight adjustment.
Trained on 4,629 trading days (2008-01 → 2026-05).
"""
import pandas as pd
import numpy as np
from pathlib import Path
import json

class AstroQuantScorer:
    """Quantitative scoring engine for Gold (XAUUSD) trading signals — V3."""
    
    # ═══════════════════════════════════════════════
    # LAYER 4: DYNAMIC SCORING WEIGHTS
    # ═══════════════════════════════════════════════
    
    SCORE_BULLISH = 'bullish'
    SCORE_BEARISH = 'bearish'
    
    # ---- STATIC WEIGHT TABLES (from 4,629-day backtest: 2008-2026) ----
    # Baseline: 47.0% bullish | Formula: (bullish_pct - 47.0) / divisor_pp
    
    # NAKSHATRA SCORES (Layer 2: Astro)
    # Weight: 3 pts max. Spread: Shatabhisha 56.1% → Mrigashira 37.4% (18.7% spread)
    NAKSHATRA_SCORES = {
        'Shatabhisha': +3.0,
        'Chitra': +3.0,
        'Mula': +2.5,
        'Ashlesha': +1.5,
        'Ashwini': +1.5,
        'Vishakha': +1.5,
        'Rohini': +1.0,
        'Punarvasu': +1.0,
        'Ardra': +1.0,
        'Purva Bhadrapada': +0.5,
        'Swati': +0.5,
        'Krittika': +0.5,
        'Purva Ashadha': +0.5,
        'Magha': +0.0,
        'Hasta': +0.0,
        'Shravana': -0.5,
        'Revati': -0.5,
        'Uttara Bhadrapada': -0.5,
        'Bharani': -1.0,
        'Jyeshtha': -1.0,
        'Pushya': -1.0,
        'Purva Phalguni': -1.0,
        'Anuradha': -1.5,
        'Uttara Ashadha': -2.0,
        'Uttara Phalguni': -2.0,
        'Dhanishta': -3.0,
        'Mrigashira': -3.0,
    }
    
    # MOON SIGN SCORES
    # Weight: 2 pts max. Spread: Libra 51.7% → Capricorn 41.9% (9.8% spread)
    MOON_SIGN_SCORES = {
        'Libra': +2.0,
        'Sagittarius': +1.5,
        'Cancer': +1.0,
        'Aquarius': +1.0,
        'Aries': +0.5,
        'Taurus': +0.0,
        'Virgo': -0.5,
        'Pisces': -0.5,
        'Gemini': -1.0,
        'Leo': -1.0,
        'Scorpio': -1.0,
        'Capricorn': -2.0,
    }
    
    # PLANET RETROGRADE SCORES
    # Deltas vs Direct: Mercury +3.6pp, Venus +2.9pp, Jupiter +1.8pp, Mars +1.1pp, Saturn -1.7pp
    RETRO_SCORES = {
        'mercury_retro': +1.5,
        'venus_retro': +1.0,
        'jupiter_retro': +0.5,
        'mars_retro': +0.5,
        'saturn_retro': -0.5,
    }
    
    # COMBUST SCORES
    # Mercury Combust 46.6% (neutral), Venus 45.4% (-1.6pp), Mars 45.3% (-1.7pp, range 26.9=1.4x)
    COMBUST_SCORES = {
        'mercury_combust': +0.0,
        'venus_combust': -0.5,
        'mars_combust': -0.5,
    }
    
    # HORA SCORES
    # Venus 49.6%, Jupiter 48.4%, Mercury 47.2%, Moon 45.1%, Mars 44.4%
    HORA_SCORES = {
        'Venus': +1.0,
        'Jupiter': +0.5,
        'Mercury': +0.0,
        'Moon': -0.5,
        'Mars': -1.0,
    }
    
    # MOON PHASE SCORES
    # First Quarter 48.8%, Waning Crescent 48.9%, etc.
    MOON_PHASE_SCORES = {
        'First Quarter': +0.5,
        'Waning Crescent': +0.5,
        'Last Quarter': +0.5,
        'Waning Gibbous': +0.0,
        'Waxing Gibbous': +0.0,
        'Waxing Crescent': -0.5,
        'Full Moon': -0.5,
        'New Moon': -0.5,
    }
    
    # NAKSHATRA LORD SCORES (from 4,629-day report section 18)
    # Rahu 51.3%, Ketu 50.8%, Jupiter 49.6%, Moon 47.7%, Mercury 47.5%, Venus 45.2%, Saturn 43.9%, Mars 43.5%, Sun 43.2%
    NAKSHATRA_LORD_SCORES = {
        'Rahu': +1.5,
        'Ketu': +1.5,
        'Jupiter': +1.0,
        'Moon': +0.5,
        'Mercury': +0.0,
        'Venus': -0.5,
        'Saturn': -1.0,
        'Mars': -1.5,
        'Sun': -1.5,
    }
    
    # ASPECT SCORES (from 4,629-day backtest, all aspects with ≥20 day samples)
    # Divisor: 3.0 pp per score unit, max ±3.0
    ASPECT_SCORES = {
        # === STRONG BULLISH (≥+2.0) ===
        'Jupiter Opposition Rahu': +3.0,
        'Jupiter Conjunction Ketu': +3.0,
        'Rahu Square Jupiter': +3.0,
        'Ketu Square Jupiter': +3.0,
        'Moon Opposition Rahu': +3.0,
        'Moon Conjunction Ketu': +3.0,
        'Sun Square Saturn': +3.0,
        'Jupiter Square Rahu': +3.0,
        'Jupiter Square Ketu': +3.0,
        'Moon Conjunction Jupiter': +2.5,
        # === MODERATE BULLISH (+1.0 to +1.5) ===
        'Rahu Conjunction Jupiter': +2.0,
        'Sun Opposition Jupiter': +2.0,
        'Moon Trine Mars': +2.0,
        'Moon Conjunction Venus': +2.0,
        'Rahu Square Mercury': +2.0,
        'Ketu Square Mercury': +2.0,
        'Sun Conjunction Saturn': +1.5,
        'Moon Square Mars': +1.5,
        'Moon Opposition Mars': +1.5,
        'Moon Square Rahu': +1.5,
        'Moon Square Ketu': +1.5,
        'Sun Conjunction Rahu': +1.5,
        'Sun Conjunction Ketu': +1.5,
        'Moon Sextile Venus': +1.5,
        'Sun Square Moon': +1.5,
        # === MILD BULLISH (+0.5 to +1.0) ===
        'Moon Sextile Jupiter': +1.0,
        'Moon Sextile Mercury': +1.0,
        'Moon Opposition Saturn': +1.0,
        'Mars Sextile Jupiter': +1.0,
        'Sun Square Jupiter': +1.0,
        'Moon Sextile Mars': +0.5,
        'Moon Conjunction Rahu': +0.5,
        'Moon Opposition Ketu': +0.5,
        'Sun Trine Moon': +0.5,
        'Sun Opposition Moon': +0.5,
        'Sun Sextile Moon': +0.5,
        'Moon Conjunction Saturn': +0.0,
        'Moon Opposition Jupiter': +0.0,
        'Sun Square Rahu': +0.0,
        'Sun Square Ketu': +0.0,
        # === MILD BEARISH (-0.5 to -1.0) ===
        'Moon Square Jupiter': -0.5,
        'Moon Opposition Mercury': -0.5,
        'Moon Trine Venus': -0.5,
        'Venus Conjunction Jupiter': -0.5,
        'Sun Opposition Mars': -0.5,
        'Mars Square Jupiter': -0.5,
        'Sun Trine Jupiter': -1.0,
        'Moon Sextile Rahu': -1.0,
        'Moon Trine Ketu': -1.0,
        'Sun Sextile Rahu': -1.0,
        'Sun Trine Ketu': -1.0,
        'Rahu Opposition Venus': -1.0,
        'Rahu Conjunction Saturn': -1.0,
        'Rahu Conjunction Venus': -1.0,
        'Rahu Conjunction Mars': -1.0,
        # === STRONG BEARISH (≤ -1.5) ===
        'Sun Square Mars': -1.0,
        'Moon Square Mercury': -1.0,
        'Sun Sextile Saturn': -1.5,
        'Rahu Square Mars': -1.5,
        'Ketu Square Mars': -1.5,
        'Rahu Opposition Mercury': -1.5,
        'Moon Opposition Venus': -1.5,
        'Sun Trine Mars': -1.5,
        'Moon Trine Mercury': -2.0,
        'Moon Square Saturn': -2.0,
        'Moon Conjunction Mercury': -2.5,
        # === EXTREME BEARISH (≤ -2.5) ===
        'Sun Sextile Jupiter': -3.0,
        'Rahu Opposition Mars': -3.0,
        'Ketu Conjunction Mars': -3.0,
        'Mars Opposition Rahu': -3.0,
        'Mars Conjunction Ketu': -3.0,
        'Mercury Trine Mars': -1.5,
        'Mercury Trine Ketu': -1.5,
        'Mercury Sextile Rahu': -1.5,
        'Mercury Conjunction Jupiter': -1.0,
        'Venus Square Mars': -1.0,
        'Mars Trine Jupiter': -1.0,
        'Moon Trine Jupiter': -1.5,
        'Moon Conjunction Mars': +0.0,
        'Venus Trine Saturn': +1.0,
        'Venus Conjunction Saturn': +1.0,
        'Mars Conjunction Rahu': -1.0,
        'Mars Opposition Ketu': -1.0,
        'Mars Square Saturn': +0.5,
        'Mars Conjunction Saturn': +0.5,
        'Saturn Sextile Rahu': -0.5,
        'Saturn Trine Ketu': -0.5,
        'Venus Sextile Rahu': +0.5,
        'Venus Trine Ketu': +0.5,
        'Jupiter Trine Rahu': +1.0,
        'Jupiter Sextile Ketu': +1.0,
        'Saturn Square Rahu': -0.5,
        'Saturn Square Ketu': -0.5,
        'Jupiter Conjunction Saturn': +0.5,
        'Venus Opposition Mars': -1.5,
        'Mercury Square Saturn': +0.5,
        'Venus Square Saturn': +1.0,
        'Mars Sextile Saturn': +0.5,
        'Mars Trine Saturn': -0.5,
        'Saturn Opposition Rahu': -0.5,
        'Saturn Conjunction Ketu': -0.5,
        'Saturn Conjunction Rahu': -0.5,
        'Saturn Opposition Ketu': -0.5,
        'Venus Square Jupiter': -0.5,
        'Venus Opposition Jupiter': +0.5,
        'Jupiter Sextile Saturn': +0.5,
        'Mercury Opposition Jupiter': +0.5,
        'Mercury Square Mars': -0.5,
        'Mercury Square Jupiter': -1.0,
        'Mercury Conjunction Saturn': -0.5,
    }
    
    # GANN SCORES (from 4,629 days)
    # Held: 38.6% bullish (-8.4pp), Breached: 48.3% (+1.3pp)
    GANN_HELD_SCORE = -3.0
    GANN_BREACHED_SCORE = 0.5
    
    # EMA SCORES
    # EMA31>113: 48.2% (+1.2pp), EMA31<113: 44.5% (-2.5pp)
    EMA_ABOVE_SCORE = 0.5
    EMA_BELOW_SCORE = -1.0
    
    # MACRO SCORES
    # DXY Bullish→Gold 33.8% (-13.2pp), DXY Bearish→Gold 59.7% (+12.7pp)
    DXY_BULLISH_SCORE = -3.0
    DXY_BEARISH_SCORE = 3.0
    
    # VENUS/MERCURY PHASE SCORES
    # Venus MS 49.5% (+2.5pp), Venus ES 44.4% (-2.6pp)
    VENUS_MORNING_STAR_SCORE = 1.0
    VENUS_EVENING_STAR_SCORE = -1.0
    # Mercury MS 47.2% (+0.2pp), Mercury ES 46.8% (-0.2pp)
    MERCURY_MORNING_STAR_SCORE = 0.0
    MERCURY_EVENING_STAR_SCORE = 0.0
    
    # VENUS × DXY CONFLUENCE
    # MS/bearish 63.1%, ES/bearish 56.3%, MS/bullish 35.1%, ES/bullish 32.5%
    VENUS_DXY_SCORES = {
        'Morning Star bearish': +3.0,
        'Evening Star bearish': +2.0,
        'Morning Star bullish': -2.5,
        'Evening Star bullish': -3.0,
    }
    
    # RSI BAND SCORES
    # Oversold 33.2%, Weak 40.1%, Strong 51.3%, Overbought 58.5%
    RSI_BAND_SCORES = {
        'Oversold (<30)': -3.0,
        'Overbought (>70)': +2.5,
        'Weak (30-50)': -1.5,
        'Strong (50-70)': +1.0,
    }
    
    # EVENT SCORES
    EVENT_HIGH_IMPACT_PENALTY = -0.5
    FOMC_NEUTRAL = 0.0
    NFP_SCORE = -0.5
    CPI_SCORE = -0.5
    ISM_MFG_SCORE = +1.0
    
    # ═══════════════════════════════════════════════
    # VOLATILITY REGIME DETECTION
    # ═══════════════════════════════════════════════
    
    @staticmethod
    def detect_volatility_regime(gold_range, volatility_label=None):
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
        if volatility_regime == 'low':
            return {
                'nakshatra': 1.0, 'moon_sign': 1.0, 'retro': 1.0,
                'combust': 0.8, 'hora': 0.5, 'moon_phase': 1.0,
                'aspects': 0.7, 'gann': 1.5, 'ema': 1.5,
                'dxy': 1.2, 'venus_phase': 0.5, 'mercury_phase': 0.5,
                'rsi': 1.0, 'venus_dxy': 1.2, 'nakshatra_lord': 1.0,
            }
        elif volatility_regime == 'high':
            return {
                'nakshatra': 1.3, 'moon_sign': 1.0, 'retro': 1.2,
                'combust': 1.5, 'hora': 0.3, 'moon_phase': 0.8,
                'aspects': 1.5, 'gann': 2.0, 'ema': 0.5,
                'dxy': 0.8, 'venus_phase': 0.8, 'mercury_phase': 0.8,
                'rsi': 1.0, 'venus_dxy': 0.8, 'nakshatra_lord': 1.0,
            }
        else:
            return {
                'nakshatra': 1.0, 'moon_sign': 1.0, 'retro': 1.0,
                'combust': 1.0, 'hora': 1.0, 'moon_phase': 1.0,
                'aspects': 1.0, 'gann': 1.0, 'ema': 1.0,
                'dxy': 1.0, 'venus_phase': 1.0, 'mercury_phase': 1.0,
                'rsi': 1.0, 'venus_dxy': 1.0, 'nakshatra_lord': 1.0,
            }
    
    # ═══════════════════════════════════════════════
    # MAIN SCORING FUNCTION
    # ═══════════════════════════════════════════════
    
    @classmethod
    def score(cls, row, volatility_regime=None):
        gold_range = row.get('gold_range')
        vol_label = row.get('volatility')
        regime = cls.detect_volatility_regime(gold_range, vol_label)
        if volatility_regime:
            regime = volatility_regime
        
        weights = cls.get_regime_weights(regime)
        
        score = 0.0
        details = {}
        max_possible = 0.0
        
        # 1. Nakshatra
        nakshatra = row.get('moon_nakshatra')
        if nakshatra and nakshatra in cls.NAKSHATRA_SCORES:
            ns = cls.NAKSHATRA_SCORES[nakshatra]
            score += ns * weights['nakshatra']
            max_possible += 3.0 * weights['nakshatra']
            details['nakshatra'] = {'value': nakshatra, 'score': ns, 'weighted': round(ns * weights['nakshatra'], 2)}
        
        # 2. Moon Sign
        moon_sign = row.get('moon_sign')
        if moon_sign and moon_sign in cls.MOON_SIGN_SCORES:
            ms = cls.MOON_SIGN_SCORES[moon_sign]
            score += ms * weights['moon_sign']
            max_possible += 2.0 * weights['moon_sign']
            details['moon_sign'] = {'value': moon_sign, 'score': ms, 'weighted': round(ms * weights['moon_sign'], 2)}
        
        # 3. Retrogrades
        retro_total = 0.0
        for planet, retro_score in cls.RETRO_SCORES.items():
            if row.get(planet, False):
                retro_total += retro_score * weights['retro']
        score += retro_total
        max_possible += 3.0 * weights['retro']
        details['retro'] = {'total': round(retro_total, 2), 'weighted': round(retro_total, 2)}
        
        # 4. Combust
        combust_total = 0.0
        for planet, comb_score in cls.COMBUST_SCORES.items():
            if row.get(planet, False):
                combust_total += comb_score * weights['combust']
        score += combust_total
        max_possible += 3.0 * weights['combust']
        details['combust'] = {'total': round(combust_total, 2), 'weighted': round(combust_total, 2)}
        
        # 5. Hora
        hora = row.get('dominant_planet_hour')
        if hora and hora in cls.HORA_SCORES:
            hs = cls.HORA_SCORES[hora] * weights['hora']
            score += hs
            max_possible += 1.0 * weights['hora']
            details['hora'] = {'value': hora, 'score': round(hs, 2)}
        
        # 6. Moon Phase
        moon_phase = row.get('moon_phase')
        if moon_phase and moon_phase in cls.MOON_PHASE_SCORES:
            mp = cls.MOON_PHASE_SCORES[moon_phase] * weights['moon_phase']
            score += mp
            max_possible += 1.0 * weights['moon_phase']
            details['moon_phase'] = {'value': moon_phase, 'score': round(mp, 2)}
        
        # 6b. Nakshatra Lord
        nakshatra_lord = row.get('nakshatra_lord')
        if nakshatra_lord and nakshatra_lord in cls.NAKSHATRA_LORD_SCORES:
            nl = cls.NAKSHATRA_LORD_SCORES[nakshatra_lord] * weights['nakshatra_lord']
            score += nl
            max_possible += 1.5 * weights['nakshatra_lord']
            details['nakshatra_lord'] = {'value': nakshatra_lord, 'score': round(nl, 2)}
        
        # 7. Aspects
        aspects_total = 0.0
        aspects_detail = []
        aspects_json = row.get('aspects_json')
        if aspects_json and not pd.isna(aspects_json) and str(aspects_json).strip() not in ['', 'nan', '[]']:
            try:
                aspects = json.loads(str(aspects_json)) if isinstance(aspects_json, str) else aspects_json
                if isinstance(aspects, list):
                    for asp in aspects:
                        p1 = asp.get('planet1', '')
                        p2 = asp.get('planet2', '')
                        asp_type = asp.get('aspect', '')
                        key = f"{p1} {asp_type} {p2}"
                        if key in cls.ASPECT_SCORES:
                            as_ = cls.ASPECT_SCORES[key] * weights['aspects']
                            aspects_total += as_
                            aspects_detail.append({'aspect': key, 'score': round(as_, 2)})
            except:
                pass
        score += aspects_total
        max_possible += 6.0 * weights['aspects']
        details['aspects'] = {'total': round(aspects_total, 2), 'details': aspects_detail}
        
        # 8. Gann Key Level
        gann_held_val = row.get('gann_held')
        if gann_held_val is None:
            gann_held_val = row.get('gann_key_level_held')
        if gann_held_val is not None:
            gs = (cls.GANN_HELD_SCORE if gann_held_val else cls.GANN_BREACHED_SCORE) * weights['gann']
            score += gs
            max_possible += 1.0 * weights['gann']
            details['gann'] = {'held': bool(gann_held_val), 'score': round(gs, 2)}
            if not gann_held_val:
                details['high_vol_alert'] = 'GANN BREACHED — expect 4x range'
        
        # 9. EMA
        ema = row.get('gold_ema_relation')
        if ema:
            es = (cls.EMA_ABOVE_SCORE if ema == 'above' else cls.EMA_BELOW_SCORE) * weights['ema']
            score += es
            max_possible += 1.0 * weights['ema']
            details['ema'] = {'relation': ema, 'score': round(es, 2)}
        
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
            details['dxy'] = {'direction': dxy_dir, 'score': round(ds, 2)}
        
        # 11. Venus Phase
        venus_dir = row.get('venus_elong_dir')
        if venus_dir:
            vs = (cls.VENUS_MORNING_STAR_SCORE if venus_dir == 'W' else cls.VENUS_EVENING_STAR_SCORE)
            vs *= weights['venus_phase']
            score += vs
            details['venus_phase'] = {'dir': venus_dir, 'score': round(vs, 2)}
        
        # 12. Mercury Phase  
        merc_dir = row.get('mercury_elong_dir')
        if merc_dir:
            ms = (cls.MERCURY_MORNING_STAR_SCORE if merc_dir == 'W' else cls.MERCURY_EVENING_STAR_SCORE)
            ms *= weights['mercury_phase']
            score += ms
            details['mercury_phase'] = {'dir': merc_dir, 'score': round(ms, 2)}
        
        # 13. Venus × DXY Confluence
        venus_dir2 = row.get('venus_elong_dir')
        dxy_dir2 = row.get('dxy_direction')
        if venus_dir2 and dxy_dir2:
            vphase = 'Morning Star' if venus_dir2 == 'W' else 'Evening Star'
            vdx_key = f"{vphase} {dxy_dir2}"
            if vdx_key in cls.VENUS_DXY_SCORES:
                vds = cls.VENUS_DXY_SCORES[vdx_key] * weights['venus_dxy']
                score += vds
                details['venus_dxy'] = {'confluence': vdx_key, 'score': round(vds, 2)}
        
        # 14. RSI Band
        rsi_val = row.get('gold_rsi_14')
        if rsi_val is not None and not pd.isna(rsi_val):
            if rsi_val < 30:
                rsi_band = 'Oversold (<30)'
            elif rsi_val < 50:
                rsi_band = 'Weak (30-50)'
            elif rsi_val < 70:
                rsi_band = 'Strong (50-70)'
            else:
                rsi_band = 'Overbought (>70)'
            if rsi_band in cls.RSI_BAND_SCORES:
                rs = cls.RSI_BAND_SCORES[rsi_band] * weights['rsi']
                score += rs
                details['rsi'] = {'band': rsi_band, 'value': rsi_val, 'score': round(rs, 2)}
        
        # 15. Mars Combust HIGH VOL penalty alert
        if row.get('mars_combust', False):
            details['mars_combust_alert'] = 'MARS COMBUST — avg range $26.9 (1.4x), high vol'
        
        # 16. Economic events
        impact = row.get('economic_impact')
        if impact == 'high':
            score += cls.EVENT_HIGH_IMPACT_PENALTY * weights['gann']
            details['eco_impact'] = 'HIGH impact economic event'
        
        # ═══════════════════════════════════════════════
        # NORMALIZE & CLASSIFY
        # ═══════════════════════════════════════════════
        
        if max_possible > 0:
            normalized = (score / max_possible) * 10
        else:
            normalized = 0.0
        
        normalized = max(-10.0, min(10.0, normalized))
        
        if normalized >= 3.0:
            signal = 'LONG'
            confidence = 'HIGH' if normalized >= 6.0 else 'MEDIUM'
        elif normalized <= -3.0:
            signal = 'SHORT'
            confidence = 'HIGH' if normalized <= -6.0 else 'MEDIUM'
        else:
            signal = 'NEUTRAL'
            confidence = 'LOW'
        
        # Market State
        if normalized >= 4.0 and regime != 'high':
            market_state = 'expansion'
        elif normalized <= -4.0 and regime != 'high':
            market_state = 'expansion'
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
                continue
        
        results_df = pd.DataFrame(results)
        
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
                'long_avg_change': round(long_signals['actual_change'].mean(), 4) if len(long_signals) > 0 else 0,
                'short_avg_change': round(short_signals['actual_change'].mean(), 4) if len(short_signals) > 0 else 0,
                'high_conf_long_win_rate': None,
                'high_conf_short_win_rate': None,
            }
            
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
    
    print("Loading data for V3 backtest...")
    dfs = []
    for f in sorted(DATA_DIR.glob("*.csv")):
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            print(f"Error: {f}: {e}")
    full_df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(full_df)} rows from {len(dfs)} CSVs")
    
    print("\nRunning Astro-Quant Scorer V3 backtest...")
    results_df, stats = AstroQuantScorer.backtest(full_df)
    
    print("\n" + "="*60)
    print("ASTRO-QUANT SCORER V3 — BACKTEST RESULTS (4,629 days: 2008-2026)")
    print("="*60)
    print(f"Total days scored: {stats['total_days']}")
    print(f"Bullish ratio: {full_df['gold_bullish'].mean()*100:.1f}%")
    print(f"LONG signals:  {stats['long_signals']}  → Win rate: {stats['long_win_rate']}%  → AvgΔ: {stats['long_avg_change']:+.4f}%")
    print(f"SHORT signals: {stats['short_signals']}  → Win rate: {stats['short_win_rate']}%  → AvgΔ: {stats['short_avg_change']:+.4f}%")
    print(f"NEUTRAL:       {stats['neutral_signals']}")
    
    if stats.get('high_conf_long_win_rate'):
        print(f"\nHIGH CONF LONG:  {stats['high_conf_long_count']} signals, Win rate: {stats['high_conf_long_win_rate']}%")
    if stats.get('high_conf_short_win_rate'):
        print(f"HIGH CONF SHORT: {stats['high_conf_short_count']} signals, Win rate: {stats['high_conf_short_win_rate']}%")
    
    if 'market_state' in results_df.columns:
        print(f"\nMarket State Distribution:")
        for state in ['expansion', 'compression', 'exhaustion', 'fear']:
            cnt = len(results_df[results_df['market_state'] == state])
            print(f"  {state}: {cnt} days ({cnt/len(results_df)*100:.1f}%)")
    
    if 'volatility_regime' in results_df.columns:
        print(f"\nVolatility Regime Distribution:")
        for reg in ['low', 'medium', 'high']:
            cnt = len(results_df[results_df['volatility_regime'] == reg])
            print(f"  {reg}: {cnt} days ({cnt/len(results_df)*100:.1f}%)")
            
    print("\n✅ V3 Backtest complete.")
