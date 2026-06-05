"""
carmen_analyst.py — Carmen AI Analysis Engine for Gold (XAUUSD) Trading

Takes raw data from run_bot.py (price, TA, Gann, Hora, Vedic transits, news)
and uses a large language model (Gemini or DeepSeek) to produce a structured
JSON analysis before report generation.

Supports two backends:
  - gemini   (google.genai)    — model: gemini-2.5-flash-lite (default)
  - deepseek (OpenAI-compat)   — model: deepseek-chat / deepseek-reasoner

Config:
  Backend chosen via CARMEN_BACKEND env var or __init__ argument.
  API keys: GEMINI_API_KEY or DEEPSEEK_API_KEY in .env
  DeepSeek custom URL: DEEPSEEK_BASE_URL (default: https://api.deepseek.com)

Output JSON schema:
{
  "bias": "BULLISH" | "BEARISH" | "NEUTRAL" | "MIXED",
  "confidence": 0.0-1.0,
  "entry": { "direction": "BUY" | "SELL" | "HOLD", "price": float, "reasoning": "string" },
  "stop_loss": float,
  "take_profit": [float, float],
  "risk_reward": float,
  "technical_assessment": { "fib_position": "", "gann_key_levels": "", "trend_strength": "", "confluence_zones": [] },
  "astro_assessment": { "moon_sentiment": "", "hora_signal": "", "key_aspects": [], "combust_warnings": [], "retrograde_notes": [] },
  "macro_context": "string",
  "key_risks": ["string"],
  "reasoning_summary": "string"
}

Usage:
    from carmen_analyst import CarmenAnalyst
    analyst = CarmenAnalyst(backend="deepseek")   # or "gemini"
    analysis = analyst.analyze(data)
"""

import os
import sys
import json
import re
import time
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Load .env from workspace root
_workspace = Path(__file__).parent
_dotenv_path = _workspace / ".env"
if _dotenv_path.exists():
    load_dotenv(_dotenv_path)


# ──────────────────────────────────────────────
# SYSTEM PROMPT — Carmen's Trading Framework
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are Carmen, a senior trading analyst specializing in Gold (XAUUSD) using a hybrid framework of:

1. W.D. Gann Theory (Square of 9, Time & Price, Fan angles)
2. Fibonacci Retracement (Kim Ssa custom levels: 0, 0.2126, 0.5, 0.618, 0.7874, 1, 1.2126, 1.5, 1.618, 1.7874)
3. Vedic Astrology (sidereal zodiac, nakshatras, planetary hours/hora, aspects, combust analysis)
4. Macro fundamentals (news, USD pressure, yields)
5. Multi-Timeframe Analysis (H4 trend + M30 entry timing)
6. Historical Correlation (4-year patreon-db statistical patterns)

CRITICAL RULES:
- ALWAYS output valid JSON only. No markdown, no explanations outside JSON.
- bias must be one of: "BULLISH", "BEARISH", "NEUTRAL", "MIXED"
- confidence must be 0.0 to 1.0 (be honest — low when signals conflict)
- entry.direction must be "BUY", "SELL", or "HOLD"
- take_profit must be an array of exactly 2 price levels [TP1, TP2]
- risk_reward = abs(TP2 - entry_price) / abs(entry_price - stop_loss)
- All reasoning must be in Vietnamese (trading terminology)
- Be specific with price levels — never vague
- If data is missing or unreliable, set confidence low and explain why

MULTI-TIMEFRAME PRIORITY (H4 > M30):
- H4 determines PRIMARY BIAS: if H4 trend is UP, BUY signals get higher confidence; if H4 is DOWN, SELL signals get higher confidence
- M30 determines ENTRY TIMING: wait for M30 pullback to support in H4 uptrend, or M30 rally to resistance in H4 downtrend
- When H4 and M30 CONTRADICT (e.g. H4 UP but M30 DOWN), reduce confidence by 15-20%. The conflict means choppy/range market.
- When H4 and M30 ALIGN (both UP or both DOWN), boost confidence by 10-15%. Alignment = stronger signal.
- H4 EMA cross (12/26) carries more weight than M30 EMA cross (31/113). Golden Cross on H4 = strong bullish bias; Death Cross = strong bearish.
- H4 Swing High/Low defines the REAL support/resistance. M30 levels are for entry precision.
- H4 Gann Fan 1x1 direction tells the medium-term trend. If H4 Fan 1x1 is sloping up, prioritize BUY setups.

HISTORICAL CORRELATION USAGE:
- The "correlation_data" section shows how this exact nakshatra+moon_sign+setup performed historically.
- nakshatra_stats.bullish_pct: if >60%, increase confidence for BUY bias; if <40%, increase confidence for BEARISH bias
- combined_stats (same nakshatra + moon sign): strongest historical signal. If 20+ days of data, weight this heavily.
- exact_matches: similar days in history. Check their close price and direction — does history repeat?
- baseline.overall_bullish_pct (~48%) is the null hypothesis. If nakshatra bullish_pct is close to 48%, don't overweight it.
- retro_stats: if a planet is retrograde AND delta_bullish is significant (>5%), factor this into the astro assessment
- ganm_key_stats: if breached_range is 2x+ held_range, the market is in breakout mode — confidence for directional calls should be HIGHER
- NEVER blindly follow correlation. Use it to VALIDATE or QUESTION your technical+astro conclusion.

ANALYSIS FRAMEWORK:
1. Multi-TF: H4 primary trend → M30 entry precision. Alignment vs conflict.
2. Technical: price vs Fibonacci levels, Gann Fan direction, Gann Date proximity, trend strength
3. Astrological: Moon sign sentiment, Hora energy, key aspects (tight orb <= 8 degrees), combust warnings
4. Historical: 4-year correlation — what does history say about this exact setup?
5. Macro: news sentiment, high-impact calendar events
6. Synthesis: where do Multi-TF + technical + astro + historical + macro agree? Where do they conflict?

CRITICAL — WHEN TO SET HOLD:
- If confidence < 0.45, ALWAYS set entry.direction = "HOLD"
- Do NOT force a BUY or SELL with weak conviction. If signals conflict, HOLD is the right call.
- If bias is NEUTRAL or MIXED, direction must be HOLD (not BUY or SELL)
- Setting a weak BUY/SELL with R:R < 1:0.5 damages trader trust. Be honest and set HOLD.
- EXCEPTION: if historical correlation shows >75% bullish for this setup AND H4 trend aligns, you may raise confidence on BUY even if M30 is choppy.
- EXCEPTION: if historical correlation shows <25% bullish (i.e. >75% bearish) AND H4 trend aligns, you may raise confidence on SELL.

CONFIDENCE CALIBRATION WITH HISTORICAL DATA:
- High confidence (0.75-1.0): H4 + M30 aligned + nakshatra bull/bear >65% + R:R > 1:2 + no conflicting aspects
- Medium confidence (0.55-0.74): Most signals align but 1-2 conflicts (e.g., H4 UP but Moon Venus Hora)
- Low confidence (0.35-0.54): Multiple conflicts between timeframes or between technical & astro
- Very low (<0.35): Don't trade. Set HOLD.

MACRO_CONTEXT FORMAT:
The macro_context field must be a detailed, specific Vietnamese analysis as bullet points covering:
- Overall gold trend this week/month (e.g., "Vàng đang trên đà giảm tuần thứ 2 liên tiếp")
- Fed/central bank policy impact (e.g., "Fed vẫn là yếu tố chính — kỳ vọng lãi suất chưa giảm tạo áp lực")
- DXY and bond yield dynamics
- Safe-haven demand / geopolitical factors
- Central bank buying flows and ETF demand
- Notable analyst forecasts if available
- Specific Fed officials or policy changes mentioned in news
- Use the news data provided to make it current, not generic
- Write as natural Vietnamese, each point on a new line starting with •

OUTPUT FORMAT (exact JSON structure — NO markdown, NO code fences):
{
  "bias": "BULLISH|BEARISH|NEUTRAL|MIXED",
  "confidence": 0.75,
  "entry": {
    "direction": "BUY|SELL|HOLD",
    "price": 4520.0,
    "reasoning": "Chi tiết lý do vào lệnh"
  },
  "stop_loss": 4470.0,
  "take_profit": [4525.0, 4735.0],
  "risk_reward": 4.2,
  "technical_assessment": {
    "fib_position": "Giá đang ở đâu so với Fibonacci",
    "gann_key_levels": "Mốc Gann quan trọng nhất",
    "trend_strength": "strong|moderate|weak",
    "confluence_zones": ["vùng 1", "vùng 2"]
  },
  "astro_assessment": {
    "moon_sentiment": "Moon sign + nakshatra impact",
    "hora_signal": "Current + next hora analysis",
    "key_aspects": ["aspect 1", "aspect 2"],
    "combust_warnings": ["warning 1"],
    "retrograde_notes": ["note 1"]
  },
  "macro_context": "News + macro summary",
  "key_risks": ["risk 1", "risk 2"],
  "reasoning_summary": "Tổng hợp ngắn gọn 3-5 câu: technical + astro + macro -> conclusion"
}

IMPORTANT: Return ONLY the raw JSON object. No backticks, no markdown, no extra text."""


# ──────────────────────────────────────────────
# DATA FORMATTER — Build the analysis prompt
# ──────────────────────────────────────────────

def build_analysis_prompt(data: dict) -> str:
    """Convert raw data dict into a structured prompt for the LLM."""
    
    lines = []
    lines.append(f"📊 PHÂN TÍCH VÀNG — {data.get('current_time', 'N/A')}")
    lines.append("=" * 60)
    
    # ── PRICE ──
    lines.append(f"\n💰 GIÁ HIỆN TẠI: ${data.get('price', 'N/A')}")
    lines.append(f"Trục Gann Cơ Sở: {data.get('gann_base', 'N/A')}")
    
    # ── TA DATA ──
    ta = data.get('ta_data')
    h4 = data.get('h4_ta_data')

    # ── MULTI-TIMEFRAME HEADER ──
    lines.append(f"\n📊 PHÂN TÍCH ĐA KHUNG THỜI GIAN (H4 + M30):")

    # ── H4 Analysis (primary trend) ──
    if h4:
        lines.append(f"\n  🔷 KHUNG H4 (Xu hướng chính — quyết định BIAS):")
        lines.append(f"  Xu hướng H4: {h4.get('trend', 'N/A')}")
        lines.append(f"  Swing High H4: ${h4.get('swing_high', 'N/A')} | Swing Low H4: ${h4.get('swing_low', 'N/A')}")
        h4_fib = h4.get('fib_analysis', {})
        h4_below = h4_fib.get('below')
        h4_above = h4_fib.get('above')
        if h4_below:
            lines.append(f"  Fibonacci H4 bên dưới: {h4_below[0]} @ ${h4_below[1]}")
        if h4_above:
            lines.append(f"  Fibonacci H4 bên trên: {h4_above[0]} @ ${h4_above[1]}")
        lines.append(f"  Gann Fan H4 1x1: ${h4.get('fan_1x1', 'N/A')} | 3x1: ${h4.get('fan_3x1', 'N/A')}")
        h4_ema_s = h4.get('ema_short')
        h4_ema_l = h4.get('ema_long')
        if h4_ema_s and h4_ema_l:
            cross = h4.get('ema_cross', '')
            lines.append(f"  EMA H4: ${h4_ema_s} / ${h4_ema_l} → {cross}")
        lines.append(f"  → H4 BIAS: {'🟢 BULLISH (tìm BUY trên M30)' if h4.get('trend') == 'UP' else '🔴 BEARISH (tìm SELL trên M30)' if h4.get('trend') == 'DOWN' else '🟡 SIDEWAYS (range-bound)'}")
    else:
        lines.append("\n  🔷 KHUNG H4: Không có dữ liệu — dùng M30 làm primary")

    # ── M30 Analysis (entry timing) ──
    if ta:
        lines.append(f"\n  🔸 KHUNG M30 (Định thời — quyết định ENTRY):")
        lines.append(f"  Xu hướng M30: {ta.get('trend', 'N/A')}")
        lines.append(f"  Swing High M30: ${ta.get('swing_high', 'N/A')} | Swing Low M30: ${ta.get('swing_low', 'N/A')}")
        
        fib_a = ta.get('fib_analysis', {})
        below = fib_a.get('below')
        above = fib_a.get('above')
        if below:
            lines.append(f"  Fibonacci M30 bên dưới: {below[0]} @ ${below[1]}")
        if above:
            lines.append(f"  Fibonacci M30 bên trên: {above[0]} @ ${above[1]}")
        
        lines.append(f"  Gann Fan M30 1x1: ${ta.get('fan_1x1', 'N/A')} | 3x1: ${ta.get('fan_3x1', 'N/A')}")
        ema_s = ta.get('ema_short') or ta.get('ema_31')
        ema_l = ta.get('ema_long') or ta.get('ema_113')
        if ema_s and ema_l:
            cross = ta.get('ema_cross') or ('GOLDEN_CROSS' if ema_s > ema_l else 'DEATH_CROSS')
            lines.append(f"  EMA M30: ${ema_s} / ${ema_l} → {cross}")

        # Multi-TF alignment check
        if h4:
            h4_trend = h4.get('trend', '')
            m30_trend = ta.get('trend', '')
            if h4_trend == m30_trend:
                lines.append(f"  ⚡ ALIGNMENT: H4 {h4_trend} + M30 {m30_trend} = TÍN HIỆU MẠNH (boost confidence)")
            else:
                lines.append(f"  ⚠️ CONFLICT: H4 {h4_trend} vs M30 {m30_trend} = GIẢM CONFIDENCE (choppy/ranging)")
    else:
        lines.append("\n  🔸 KHUNG M30: Không có dữ liệu TA")
    
    # ── GANN LEVELS ──
    res = data.get('gann_resistances', [])
    sup = data.get('gann_supports', [])
    if res:
        res_str = ", ".join([f"${r['price']} ({r['angle']}°)" for r in res])
        lines.append(f"\n🔺 GANN KHÁNG CỰ: {res_str}")
    if sup:
        sup_str = ", ".join([f"${s['price']} ({s['angle']}°)" for s in sup])
        lines.append(f"🔻 GANN HỖ TRỢ: {sup_str}")
    
    # ── GANN DATE ──
    gann_dates = data.get('gann_dates', [])
    nearest = data.get('nearest_gann_date')
    if gann_dates:
        lines.append(f"\n📅 GANN DATE CYCLE (anchor: {data.get('gann_anchor_date', 'N/A')}):")
        for d in gann_dates:
            lines.append(f"  {d['target_date']} - {d['angle']} (+{d['days_added']} ngày)")
        if nearest:
            lines.append(f"  -> Sắp: {nearest.get('target_date', 'N/A')} ({nearest.get('angle', 'N/A')}) còn {nearest.get('days_remaining', '?')} ngày")
    
    # ── HORA ──
    hora = data.get('hora', {})
    if hora:
        lines.append(f"\n⏰ PLANETARY HORA:")
        lines.append(f"  Ngày sao: {hora.get('astrological_day', 'N/A')}")
        lines.append(f"  Giờ hiện tại: {hora.get('hora', 'N/A')} Hora ({hora.get('hora_start', '')} - {hora.get('hora_end', '')})")
        lines.append(f"  Độ dài giờ: {hora.get('hora_length_mins', '?')} phút")
        lines.append(f"  Ban ngày: {'Yes' if hora.get('is_daytime') else 'No'}")
    
    # ── VEDIC PLANETS ──
    planets = data.get('vedic_planets', {})
    if planets and 'error' not in planets:
        lines.append(f"\n🌌 VEDIC ASTROLOGY - HÀNH TINH:")
        for planet, pos in planets.items():
            lines.append(f"  {planet}: {pos}")
    
    # ── ASTRO REPORT (deep analysis from astro_engine) ──
    astro_report = data.get('astro_report', '')
    if astro_report:
        lines.append(f"\n🌌 PHÂN TÍCH THIÊN VĂN CHI TIẾT:")
        lines.append(astro_report)
    
    # ── ASTRO ANALYSIS (structured) ──
    astro_analysis = data.get('astro_analysis', {})
    if astro_analysis and isinstance(astro_analysis, dict):
        lines.append(f"\n🌌 PHÂN TÍCH MOON CHI TIẾT:")
        for key, val in astro_analysis.items():
            if isinstance(val, dict):
                for k2, v2 in val.items():
                    lines.append(f"  {key}.{k2}: {v2}")
            else:
                lines.append(f"  {key}: {val}")
    
    # ── HISTORICAL CORRELATION ──
    corr = data.get('correlation_data')
    if corr and not corr.get('error'):
        lines.append(f"\n📊 CORRELATION LỊCH SỬ (4 NĂM DỮ LIỆU):")

        baseline = corr.get('baseline', {})
        if baseline:
            lines.append(f"  Baseline toàn thị trường: {baseline.get('overall_bullish_pct', 50)}% bullish, avg change {baseline.get('overall_avg_change', 0):+.3f}%")

        nak = corr.get('nakshatra_stats')
        if nak:
            delta = round(nak['bullish_pct'] - baseline.get('overall_bullish_pct', 50), 1)
            lines.append(f"  Nakshatra {nak['nakshatra']}: {nak['bullish_pct']}% bullish ({nak['total_days']} ngày) — delta {'+' if delta > 0 else ''}{delta}% vs baseline")
            lines.append(f"    Avg change: {nak['avg_change_pct']:+.2f}% | Avg range: ${nak['avg_range']:.1f} | Phản ứng phổ biến: {nak.get('dominant_reaction', [['N/A','']])[0][0]}")

        ms = corr.get('moon_sign_stats')
        if ms:
            lines.append(f"  Moon {ms['sign']}: {ms['bullish_pct']}% bullish ({ms['total_days']} ngày) | Avg: {ms['avg_change_pct']:+.2f}%")

        combo = corr.get('combined_stats')
        if combo:
            lines.append(f"  ⚡ COMBO {nak.get('nakshatra', '?')} + Moon {ms.get('sign', '?')}: **{combo['bullish_pct']}% bullish** ({combo['total_days']} ngày) — {'🟢 STRONG BULLISH' if combo['bullish_pct'] >= 60 else '🔴 STRONG BEARISH' if combo['bullish_pct'] <= 40 else '🟡 NEUTRAL'}")

        retro = corr.get('retro_stats')
        if retro:
            sig = [(p, s) for p, s in retro.items() if abs(s['delta_bullish']) >= 3]
            if sig:
                lines.append(f"  ℞ Retrograde effects:")
                for planet, s in sig:
                    lines.append(f"    {planet} retro: {s['retro_bullish']}% vs direct: {s['direct_bullish']}% (delta {s['delta_bullish']:+.1f}%)")

        matches = corr.get('exact_matches', [])
        if matches:
            lines.append(f"  🔍 Top similar days in history:")
            for m in matches[:3]:
                lines.append(f"    {m['date']}: ${m['close']:.1f} | {'🟢' if m['bullish'] else '🔴'} {m['change_pct']:+.2f}% | {m.get('volatility', '')} | {m.get('reaction', '')}")

        gk = corr.get('gann_key_stats')
        if gk:
            ratio = gk['breached_avg_range'] / max(gk['held_avg_range'], 1)
            lines.append(f"  🌀 Gann Key: Held range ${gk['held_avg_range']:.1f} vs Breached ${gk['breached_avg_range']:.1f} ({ratio:.1f}x)")

        lines.append(f"  💡 Dùng correlation để VALIDATE hoặc QUESTION kết luận technical + astro.")

    # ── MACRO NEWS ──
    macro = data.get('macro_calendar', [])
    if macro and isinstance(macro, list):
        lines.append(f"\n📰 TIN TỨC VĨ MÔ:")
        for item in macro:
            if isinstance(item, dict):
                lines.append(f"  . {item.get('title', item.get('info', 'N/A'))}")
    
    # ── MARKET NEWS ──
    market_news = data.get('market_news', [])
    if market_news and isinstance(market_news, list):
        lines.append(f"\n📰 TIN TỨC THỊ TRƯỜNG:")
        for item in market_news:
            if isinstance(item, dict):
                lines.append(f"  . {item.get('title', 'N/A')}")
                summary = item.get('summary', '')
                if summary:
                    lines.append(f"    {summary[:200]}")
    
    return "\n".join(lines)


# ──────────────────────────────────────────────
# ERROR RESPONSE BUILDER
# ──────────────────────────────────────────────

def _error_response(message: str, price: float = 0) -> dict:
    """Build a safe fallback dict when analysis fails."""
    return {
        "error": message,
        "bias": "NEUTRAL",
        "confidence": 0.0,
        "entry": {"direction": "HOLD", "price": price, "reasoning": f"Lỗi: {message}"},
        "stop_loss": 0,
        "take_profit": [0, 0],
        "risk_reward": 0,
        "technical_assessment": {"fib_position": "", "gann_key_levels": "", "trend_strength": "weak", "confluence_zones": []},
        "astro_assessment": {"moon_sentiment": "", "hora_signal": "", "key_aspects": [], "combust_warnings": [], "retrograde_notes": []},
        "macro_context": "",
        "key_risks": [f"AI analysis unavailable: {message}"],
        "reasoning_summary": f"Không thể phân tích — {message}"
    }


def _parse_json_response(text: str, data: dict) -> dict:
    """Try to parse JSON from LLM response, with fallbacks."""
    try:
        clean = text.strip()
        # Strip code fences if present
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1]).strip()
        
        analysis = json.loads(clean)
        return analysis
    
    except json.JSONDecodeError:
        # Fallback: extract JSON object from text
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        return _error_response(f"Failed to parse LLM response as JSON", data.get('price', 0))


# ──────────────────────────────────────────────
# BACKEND: GEMINI (via google.genai)
# ──────────────────────────────────────────────

def _call_gemini(system_prompt: str, user_prompt: str, model_name: str, api_key: str) -> str:
    """Call Google Gemini and return raw text."""
    from google import genai
    from google.genai import types
    
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=8192,
        ),
    )
    return response.text.strip()


# ──────────────────────────────────────────────
# BACKEND: DEEPSEEK (OpenAI-compatible via httpx)
# ──────────────────────────────────────────────

def _call_deepseek(system_prompt: str, user_prompt: str, model_name: str,
                    api_key: str, base_url: str) -> str:
    """Call DeepSeek (or any OpenAI-compatible API) and return raw text."""
    import httpx
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 8192,
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    url = f"{base_url.rstrip('/')}/chat/completions"
    
    with httpx.Client(timeout=120) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
    
    choices = result.get("choices", [])
    if not choices:
        raise RuntimeError(f"DeepSeek returned no choices: {result}")
    
    return choices[0]["message"]["content"].strip()


# ──────────────────────────────────────────────
# CARMEN ANALYST CLASS
# ──────────────────────────────────────────────

class CarmenAnalyst:
    """
    LLM-powered analysis engine for Gold (XAUUSD).
    Supports Gemini (default) and DeepSeek backends.
    
    Backend is set via:
      1. __init__(backend=...) argument
      2. CARMEN_BACKEND env var ("gemini" or "deepseek")
      3. Default: "gemini"
    """
    
    MODEL_MAP = {
        "gemini":   "gemini-2.5-flash-lite",
        "deepseek": "deepseek-chat",
    }
    
    def __init__(self, backend=None, model_name=None, api_key=None, base_url=None):
        """
        Initialize Carmen Analyst.
        
        Args:
            backend: "gemini" or "deepseek" (default: CARMEN_BACKEND env or "gemini")
            model_name: e.g. "gemini-2.5-flash", "deepseek-chat", "deepseek-reasoner"
                        (default: per MODEL_MAP)
            api_key: API key. Falls back to GEMINI_API_KEY or DEEPSEEK_API_KEY env.
            base_url: Base URL for DeepSeek (default: DEEPSEEK_BASE_URL env or
                      https://api.deepseek.com)
        """
        self.backend = backend or os.environ.get("CARMEN_BACKEND", "gemini")
        self.model_name = model_name or self.MODEL_MAP.get(self.backend, "gemini-2.5-flash-lite")
        
        if self.backend == "gemini":
            self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not set. Add to .env or pass api_key.")
            self.base_url = None  # Gemini uses its own SDK
        elif self.backend == "deepseek":
            self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
            if not self.api_key:
                raise ValueError("DEEPSEEK_API_KEY not set. Add DEEPSEEK_API_KEY to .env or pass api_key.")
            self.base_url = base_url or os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        else:
            raise ValueError(f"Unknown backend: {self.backend}. Use 'gemini' or 'deepseek'.")
    
    def analyze(self, data: dict) -> dict:
        """
        Analyze raw market data and return structured JSON analysis.
        
        Args:
            data: Output from run_bot.get_report_data()
        
        Returns:
            dict with bias, confidence, entry, SL, TP, assessments, reasoning
        """
        user_prompt = build_analysis_prompt(data)
        price = data.get('price', 0)
        
        print(f"🪐 Carmen AI ({self.backend}/{self.model_name}) analyzing...", file=sys.stderr)
        
        try:
            if self.backend == "gemini":
                text = _call_gemini(SYSTEM_PROMPT, user_prompt, self.model_name, self.api_key)
            else:
                text = _call_deepseek(SYSTEM_PROMPT, user_prompt, self.model_name,
                                      self.api_key, self.base_url)
            
            analysis = _parse_json_response(text, data)
            
            bias = analysis.get('bias', 'N/A')
            conf = analysis.get('confidence', 0)
            print(f"🪐 Analysis complete. Bias: {bias} | Confidence: {conf}", file=sys.stderr)
            
            return analysis
        
        except Exception as e:
            print(f"⚠️ Carmen AI error: {e}", file=sys.stderr)
            return _error_response(str(e), price)
    
    def analyze_with_cache(self, data: dict, cache_ttl_seconds=300) -> dict:
        """
        Analyze with simple file cache to avoid duplicate API calls.
        
        Args:
            data: Output from run_bot.get_report_data()
            cache_ttl_seconds: Cache lifetime (default 5 min)
        
        Returns:
            Analysis dict (from cache if valid, otherwise fresh)
        """
        cache_path = os.path.join(os.path.dirname(__file__), ".carmen_cache.json")
        
        try:
            if os.path.exists(cache_path):
                with open(cache_path, 'r') as f:
                    cache = json.load(f)
                
                cache_age = time.time() - cache.get('timestamp', 0)
                if cache_age < cache_ttl_seconds:
                    cached_price = cache.get('price', 0)
                    current_price = data.get('price', 0)
                    if abs(float(cached_price) - float(current_price)) < 5:
                        return cache.get('analysis', {})
        except:
            pass
        
        # Fresh analysis
        analysis = self.analyze(data)
        
        # Save to cache
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'price': data.get('price', 0),
                    'analysis': analysis
                }, f)
        except:
            pass
        
        return analysis


# ──────────────────────────────────────────────
# CLI TEST
# ──────────────────────────────────────────────

if __name__ == "__main__":
    from run_bot import get_report_data
    
    print("🪐 Fetching market data...")
    data = get_report_data()
    
    # Detect backend
    backend = os.environ.get("CARMEN_BACKEND", "deepseek")
    print(f"🪐 Backend: {backend} (set CARMEN_BACKEND env to switch)")
    
    print("🪐 Running Carmen analysis...")
    try:
        analyst = CarmenAnalyst(backend=backend)
        analysis = analyst.analyze(data)
        
        print(f"\n{'='*60}")
        print(f"🪐 CARMEN ANALYSIS RESULT [{backend}/{analyst.model_name}]")
        print(f"{'='*60}")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        print(f"{'='*60}")
    except ValueError as e:
        print(f"\n⚠️ {e}")
        print(f"\nTo test with DeepSeek:")
        print(f"  export DEEPSEEK_API_KEY='your-key-here'")
        print(f"  export CARMEN_BACKEND=deepseek")
        print(f"  python3 carmen_analyst.py")
        print(f"\nTo test with Gemini:")
        print(f"  export GEMINI_API_KEY='your-key-here'")
        print(f"  export CARMEN_BACKEND=gemini")
        print(f"  python3 carmen_analyst.py")
